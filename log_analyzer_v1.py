import os
import platform  
from dotenv import load_dotenv    
import google.generativeai as genai

print("Ai assistance for analysic logs ")
print("-------------------------")
print("Loading conf from .env")
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")


if not api_key :
    print("GEMINI_API_KEY Not found")
    print("Check value of GEMINI_API_KEY in .env file")
    exit()

print("Api value Detected")

#init Gemini using key
try:
    genai.configure(api_key=api_key)
    print("Api Key successfuly initialized")
except Exception as e:
    print("Err during Set api key")
    print("check Api Value Or you connection ")
    exit()

#Select Model and log Describtion

#Check acccessable modeles using my key
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methids:
        print(m.name)

MODEL_NAME='gemini-1.5-flash-latest'
print(f"you are using :{MODEL_NAME}")

try:
    model =genai.GenerativeModel(MODEL_NAME)
    print(f"{MODEL_NAME} successfuly Loaded")
except Exception as e:
    print (f"err in Loading {e}")
    exit()

def get_default_log_paths():
    paths = []
    if platform.system() == "Linux":
        paths = [
            "/var/log/auth.log",
            "/var/log/secure",
            "/var/log/syslog",
            "/var/log/messages",
            "/var/log/nginx/access.log",
            "/var/log/nginx/error.log",
            "/var/log/apache2/access.log",
            "/var/log/apache2/error.log",
            "/var/log/httpd/access_log",
            "/var/log/httpd/error_log",
        ]

    return paths
        
def find_available_logs(log_paths_to_check):
    available_logs = []
    print("\n Check available codes")
    for log_path in log_paths_to_check:
        if os.path.exists(log_path) and os.path.isfile(log_path) and os.access(log_path, os.R_OK):
            available_logs.append(log_path)
            print(f"{log_path} Detected")
        else:
            print(f"{log_path} Not Detected")
    return available_logs

def choos_log_file(available_logs):
    if not available_logs:
        print("\n i dont find readable log files")
        return None
    
    if len(available_logs) == 1:
        print(f"file for analysis {available_logs[0]}")
        return available_logs[0]
    

    print(f"PLZ select file for analysis {available_logs[0]}")
    for i, log_file in enumerate(available_logs):
        print(f"{i+1}.{log_file}")

    while True:
        try:
            choice = int(input("Enter File Num"))
            if 1 <= choice<=len(available_logs):
                selected_log = available_logs[choice-1]
                print(f" selected file:{selected_log}")
                return selected_log
            else:
                print("number is not valid enter Int From List")

        except ValueError:
            print("input isnt valid")

def read_log_content(file_path, num_lines= 100):
    try:
        with open(file_path, 'r' , encoding='utf-8' , errors='ignore') as f:
            lines = f.readline()
            log_content_lines = lines[-num_lines:]
            log_content = "".join(log_content_lines)
            if not log_content:
                print(f"{file_path} is Empty.")
                return None
            print(f"about {len(log_content_lines)} readed from {file_path} ")
            return log_content
    except FileNotFoundError:
        print(f"file Not found {file_path}")
        return None
    except PermissionError:
        print("Permission Err")
        return None
    except Exception as e :
        print("err in Reading file {e}")
        return None
    
# Logic
default_paths = get_default_log_paths()
if not default_paths:
    print("i dont have path for this Env")
    exit()

found_logs = find_available_logs(default_paths)
selected_log_files = choos_log_file(found_logs)

if not selected_log_files:
    exit()

log_data_to_analyze = read_log_content(selected_log_files , num_lines =150)
if not log_data_to_analyze:
    print("Ther is notting for analyze")
    exit()
print(" log content ready for analyze")

prompt_text = f"""
You are an expert AI security log analyst.
Your task is to meticulously analyze the provided log entries from the file '{selected_log_files}'.
Identify any suspicious activities, anomalies, errors, or notable security-related events.

For each significant event you identify, please provide:
1.  A concise description of the event.
2.  The relevant log line(s) that indicate this event.
3.  An estimated severity level (e.g., Informational, Low, Medium, High, Critical).
4.  (If applicable) Any recommended immediate actions or areas for further investigation for a system administrator.

After analyzing all entries, provide a final summary of the most important findings and an overall assessment of the security posture indicated by this log snippet.
Indicate if there are specific patterns (e.g., repeated failed logins from a specific IP, unusual port scanning attempts, successful privilege escalations).

Log entries to analyze:
---
{log_data_to_analyze}
---
Your detailed analysis:
"""
print("prompt is ready.")

print("\n proccessing ....")
try:
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt_text)

    #show res
    print("\n--- ✅ Respond Gemini API ---")
    print(response.text)

except Exception as e:
    # Erro handeling
    print(f"erro: {e}")
    error_message = str(e).lower()
    if "api key not valid" in error_message or "permission_denied" in error_message:
        print("You dont have access to this model or key is not valid")
    elif "rate limit" in error_message or "quota" in error_message:
        print("(rate limit/quota)")
    elif "model_not_found" in error_message or "not found" in error_message and "model" in error_message:
        print(f"Model Err'{MODEL_NAME}")
    elif "deadline_exceeded" in error_message:
        print("Time out Gemini API")
    else:
        print("I dont have any idea whats wrong :))")

print("\n--- finished  ---")