import subprocess
import os

def analyze_with_semgrep(owner_name, repo_name):
    # Percorso completo di Semgrep su Windows
    SEM_PATH = r"C:\Users\Utente\AppData\Local\Programs\Python\Python313\Scripts\semgrep.exe"
    
    repo_dir = os.path.join(".", "repos", repo_name)

    try:
       
        result = subprocess.run(
            [SEM_PATH, "--config=auto", "--json", repo_dir],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace" 
        )

        if result.returncode != 0:
            print(f"Semgrep failed for {repo_name}:")
            print(result.stderr)
            return None

        semgrep_output = result.stdout
        print(f"Semgrep findings for {repo_name}:")
        print(semgrep_output)

        return semgrep_output

    except FileNotFoundError:
        print("Errore: semgrep.exe non trovato. Controlla il percorso SEM_PATH.")
        return None
    except Exception as e:
        print(f"Errore in analyze_with_semgrep: {e}")
        return None
