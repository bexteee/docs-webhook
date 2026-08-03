from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, hmac, subprocess, shutil
import psycopg2

app = Flask(__name__)

load_dotenv()
webhook_key = os.getenv("WEBHOOK_SECRET")

@app.route('/deploy', methods=['POST'])
def deploy():
  database_url = os.getenv("DATABASE_URL")

  with psycopg2.connect(database_url) as conn:
    with conn.cursor() as cur:

      cur.execute("INSERT INTO webhook_events (status) VALUES ('pending') RETURNING id;")
      new_id = cur.fetchone()[0]
      conn.commit()

      auth_header = request.headers.get('Authorization')

      if auth_header is None:
        cur.execute("UPDATE webhook_events SET status = 'unauthorized' , finished_at = NOW() WHERE id = %s", (new_id,))

        conn.commit()

        return jsonify({"status": "not received"}), 401

      full_key = auth_header.split()

      if len(full_key) < 2:
        cur.execute("UPDATE webhook_events SET status = 'malformed' , finished_at = NOW() WHERE id = %s", (new_id,))

        conn.commit()

        return jsonify({"status": "invalid list"}), 400

      if hmac.compare_digest(webhook_key, full_key[1]): # comparacao da ssh key verdadeira com o que esta na string full_key
        result = run_deploy()

        if result is True:
          cur.execute("UPDATE webhook_events SET status = 'authorized', finished_at = NOW() WHERE id = %s", (new_id,))

          conn.commit()

          return jsonify({"status" : "received"}), 200
        else:
          cur.execute("UPDATE webhook_events SET status = 'failed', error_message = %s , finished_at = NOW() WHERE id = %s", (result, new_id))

          conn.commit()

          return jsonify({"status" : "Internal Server Error"}), 500

      cur.execute("UPDATE webhook_events SET status = 'unauthorized' , finished_at = NOW() WHERE id = %s", (new_id,))

      conn.commit()

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