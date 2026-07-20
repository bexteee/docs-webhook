from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, hmac, subprocess, shutil

app = Flask(__name__)

load_dotenv()
webhook_key = os.getenv("WEBHOOK_SECRET")

@app.route('/deploy', methods=['POST'])
def deploy():
  auth_header = request.headers.get('Authorization')

  if auth_header is None:
    return jsonify({"status": "not received"}), 401
  
  full_key = auth_header.split()

  if len(full_key) < 2:
    return jsonify({"status": "invalid list"}), 400
  
  if hmac.compare_digest(webhook_key, full_key[1]):
    result = run_deploy()

    if result is True:
      return jsonify({"status" : "received"}), 200
    else:
      return jsonify({"status" : "Internal Server Error"}), 500
  
  return jsonify({"status" : "not received"}), 401

def run_deploy():
  try:
    subprocess.run(["git", "pull"], cwd="/root/apps/startup-docs")
    subprocess.run(["/root/apps/startup-docs/.venv/bin/mkdocs", "build"], cwd="/root/apps/startup-docs")

    shutil.copytree("/root/apps/startup-docs/site", "/var/www/html_new")

    if os.path.exists("/var/www/html_old"):
      shutil.rmtree("/var/www/html_old")

    os.rename("/var/www/html", "/var/www/html_old")
    os.rename("/var/www/html_new", "/var/www/html")

    return True

  except Exception as e:
    error = str(e)
    return error
  
if __name__ == "__main__":
  app.run()