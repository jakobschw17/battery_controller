# =================================================================================
# WEB SERVER AND SCHEDULER (File: app.py) - TIME DISPLAY FIX
# =================================================================================
import os
import uuid
from flask import Flask, jsonify, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from inverter_control import (
    charge_from_grid,
    dont_discharge_battery,
    normal,
    get_battery_percentage,
    INVERTER_IP
)

app = Flask(__name__)

db_path = os.path.join(os.path.dirname(__file__), 'jobs.sqlite')
jobstores = {
    'default': SQLAlchemyJobStore(url=f'sqlite:///{db_path}')
}

scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

def run_scheduled_job(action, power_kw):
    """A single function the scheduler can call to run any inverter action."""
    print(f"SCHEDULER RUNNING: Action: {action}, Power: {power_kw} kW")
    if action == 'charge':
        charge_from_grid(power_kw)
    elif action == 'stop_discharge':
        dont_discharge_battery()
    elif action == 'normal':
        normal()

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control_inverter():
    """Handles commands from the manual control buttons."""
    command = request.form.get('action')
    power_kw = request.form.get('power', type=float, default=0.0)

    if command == 'charge':
        charge_from_grid(power_kw)
        message = f"Charging from grid at {power_kw} kW"
    elif command == 'stop_discharge':
        dont_discharge_battery()
        message = "Battery discharge prevented"
    elif command == 'normal':
        normal()
        message = "Inverter set to normal mode"
    else:
        return jsonify({"status": "error", "message": "Unknown command"}), 400
    
    return jsonify({"status": "success", "message": message})

@app.route('/status')
def status():
    """Provides the current battery percentage."""
    soc = get_battery_percentage(INVERTER_IP)
    if soc is not None:
        return jsonify({"soc": soc})
    else:
        return jsonify({"error": "Failed to read SoC"}), 500

@app.route('/schedule/add', methods=['POST'])
def add_schedule():
    """Adds a new scheduled job."""
    data = request.json
    hour = int(data['time'].split(':')[0])
    minute = int(data['time'].split(':')[1])
    action = data['action']
    power = float(data.get('power', 0.0))
    job_id = str(uuid.uuid4())
    
    if action == 'charge':
        job_name = f"Charge at {power}kW"
    else:
        job_name = action.replace('_', ' ').title()

    scheduler.add_job(
        run_scheduled_job,
        trigger='cron',
        hour=hour,
        minute=minute,
        args=[action, power],
        id=job_id,
        name=job_name
    )
    return jsonify({"status": "success", "message": "Job scheduled!"})

@app.route('/schedule/list')
def list_schedules():
    """Returns a list of all scheduled jobs."""
    jobs = []
    try:
        # **BUG FIX**: Corrected the indexes to get hour and minute.
        # Index 5 is 'hour', Index 6 is 'minute'.
        sorted_jobs = sorted(scheduler.get_jobs(), key=lambda j: (str(j.trigger.fields[5]), str(j.trigger.fields[6])))
        for job in sorted_jobs:
            hour = str(job.trigger.fields[5])
            minute = int(str(job.trigger.fields[6]))
            jobs.append({
                "id": job.id,
                "name": job.name,
                "time": f"{hour}:{minute:02d}"
            })
    except Exception as e:
        print(f"Could not retrieve jobs: {e}")
        
    return jsonify(jobs)

@app.route('/schedule/delete', methods=['POST'])
def delete_schedule():
    """Deletes a job by its ID."""
    data = request.json
    job_id = data['id']
    try:
        scheduler.remove_job(job_id)
        message = "Job deleted."
    except Exception as e:
        message = f"Error deleting job: {e}"
        print(message)
    return jsonify({"status": "success", "message": message})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
