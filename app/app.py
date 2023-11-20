# app.py
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
import threading
import subprocess
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


import os

def update_simc_file(content, simc_file_path, output_directory):
    lines = content.split('\n')

    start_index = next(i for i, line in enumerate(lines) if "# Actors" in line)
    end_index = next(i for i, line in enumerate(lines) if "# Simulation Options" in line)

    i = start_index + 1
    while i < end_index:
        line = lines[i].strip()
        if line.startswith("#"):
            comment_content = line.split('#')[1].strip()
            i += 1
            if i < end_index:
                next_line = lines[i]
                parts = next_line.split('"')
                if len(parts) > 1:
                    # Extracting the last part after the last '/'
                    last_part = parts[1].rsplit('/', 1)[-1]
                    if last_part and not last_part.endswith('+'):
                        last_part = '/' + last_part  # Prepend '/' if last part exists and not ending with '+'
                    parts[1] = comment_content + last_part
                    lines[i] = '"'.join(parts)
        else:
            i += 1

    modified_content = '\n'.join(lines)

    # Append additional lines for output formats
    html_line = f'html={os.path.join(output_directory, "results.html")}\n'
    log_line = f'output={os.path.join(output_directory, "log.txt")}\n'
    json_line = f'json2={os.path.join(output_directory, "report.json")}\n'
    hosted_html_line = 'hosted_html=1\n'
    report_details_line = 'report_details=0\n'
    report_precision_line = 'report_precision=2\n'
    log_line = 'log=1\n'
    additional_content = html_line + log_line + json_line + hosted_html_line + report_details_line + report_precision_line + log_line

    with open(simc_file_path, 'w') as file:
        file.write(modified_content + '\n' + additional_content)

    return True



def run_simc_script(executable_path, simc_file_path, sid):
    command = [executable_path, simc_file_path]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                socketio.emit('output', {'data': output.strip()}, to=sid)
        process.communicate()
        if process.returncode == 0:
            socketio.emit('status', {'data': 'Simulation completed successfully'}, to=sid)
            socketio.emit('simulation_complete', {'url': '/results.html'}, to=sid)
        else:
            socketio.emit('status', {'data': 'Simulation encountered an error'}, to=sid)
    except Exception as e:
        socketio.emit('output', {'data': str(e)}, to=sid)
        socketio.emit('status', {'data': 'Failed to execute simulation'}, to=sid)


# Utility functions for SIMC operations
def get_simc_input_path(filename='john.simc'):
    # Return the path to the simulation input file
    return os.path.join('simulations', 'inputs', filename)

def get_simc_output_path(filename='results.html'):
    # Return the path to the simulation output file
    return os.path.join('simulations', 'outputs', filename)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results.html')
def results():
    output_directory = os.path.join(app.root_path, 'simulations', 'outputs')
    return send_from_directory(output_directory, 'results.html')


@socketio.on('update_simc_file')
def handle_update_simc(data):
    content = data['simc_data']

    # Get the directory of the current script (app.py) then go up one level to the 'python_simc' directory
    base_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    print(base_directory)

    # Now define the paths relative to the base_directory
    simc_file_path = os.path.join(base_directory, 'app', 'simulations', 'inputs', 'john.simc')
    executable_path = os.path.join(base_directory, 'Simc', 'simc.exe')
    output_directory = os.path.join(base_directory, 'app', 'simulations', 'outputs')

    print(simc_file_path)
    print(executable_path)
    print(output_directory)

    if update_simc_file(content, simc_file_path,output_directory):
        sid = request.sid
        socketio.emit('status', {'data': 'File updated, running simulation...'}, to=sid)
        thread = threading.Thread(target=run_simc_script, args=(executable_path, simc_file_path, sid))
        thread.start()
    else:
        socketio.emit('status', {'data': 'Error: Failed to update SIMC file.'}, to=sid)

if __name__ == '__main__':
    socketio.run(app, debug=False)
