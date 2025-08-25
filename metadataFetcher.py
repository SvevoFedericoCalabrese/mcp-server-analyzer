import requests
from datetime import datetime
import json
import os
from semgrep_analyzer import analyze_with_semgrep

GITHUB_API = "https://api.github.com/repos"
FILE_NAME = "repos.json"
FILE_REPO_DATA = "repos_data.json"

repo_list = []

class Repo: 
    def __init__(self, owner_name, repo_name):
        self.owner_name = owner_name
        self.repo_name = repo_name

    def to_dict(self):
        return {"owner": self.owner_name, "repo": self.repo_name}

    @staticmethod
    def from_dict(d):
        return Repo(d["owner"], d["repo"])


def save_repos():
    with open(FILE_NAME, "w") as f:
        json.dump([r.to_dict() for r in repo_list], f, indent=2)

def save_data_on_file(jsonData):

    with open(FILE_REPO_DATA, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []


        exists = any(repo["repo_owner"] == jsonString[0]["repo_owner"] and repo["repo_name"] == jsonString[0]["repo_name"] for repo in data)

        if not exists:
            data.extend(jsonData) 
            with open(FILE_REPO_DATA, "w") as f:
                json.dump(data, f, indent=4)
    



def load_repos():
    global repo_list
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            data = json.load(f)
            repo_list = [Repo.from_dict(d) for d in data]


def get_repo_metadata(owner, repo):
    url = f"{GITHUB_API}/{owner}/{repo}"
    r = requests.get(url)
    data = r.json()
    
    metadata = {
        "full_name": data.get("full_name"),
        "description": data.get("description"),
        "license": data.get("license", {}).get("name"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues": data.get("open_issues_count"),
        "language": data.get("language"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "pushed_at": data.get("pushed_at")
    }
    return metadata


def get_commit_frequency(owner, repo):
    url = f"{GITHUB_API}/{owner}/{repo}/commits"
    r = requests.get(url, params={"per_page": 100})
    commits = r.json()
    dates = [datetime.strptime(c["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ") for c in commits if "commit" in c]
    if not dates:
        return 0
    delta_days = (max(dates) - min(dates)).days or 1
    return round(len(dates) / delta_days * 7, 2)  # commits per settimana


def get_contributors(owner, repo):
    url = f"{GITHUB_API}/{owner}/{repo}/contributors"
    r = requests.get(url)
    return len(r.json())


def add_to_repoList(owner: str, repo: str):
    new_repo = Repo(owner, repo)
    repo_list.append(new_repo)
    save_repos()  

#function used to evaluate the repo based on metadaat collected from git and the static analysis made with semgrep 
def evaluate_repo(meta, freq, contrib, semgrep_results_dict):
    score = 0
    reasons = []

    # number of stars 
    if meta.get("stars", 0) > 50:
        score += 2
        reasons.append("More than 50 stars")
    elif meta.get("stars", 0) > 10:
        score += 1
        reasons.append("Between 50 and 10 stars")
    else:
        reasons.append("Less than 10 stars")

    #  Contributors
    if contrib > 5:
        score += 2
        reasons.append("More than 5 contibutors")
    elif contrib > 1:
        score += 1
        reasons.append("Between 2 and 5 contributors")
    else:
        reasons.append("Single contributor")

    # Commit frequency
    if freq > 2:
        score += 2
        reasons.append("Frequent commits")
    elif freq > 0.5:
        score += 1
        reasons.append("Moderate amount of commits")
    else:
        reasons.append("Most likely inactive")

    # Semgrep analysis
    issues = len(semgrep_results_dict.get("results", [])) if semgrep_results_dict else 0
    if issues == 0:
        score += 2
        reasons.append("No issue found with Semgrep")
    elif issues < 5:
        score += 1
        reasons.append("Few issues found Semgrep")
    else:
        reasons.append("Many issues found withSemgrep")

    # Valutazione finale
    if score >= 6:
        verdict = "✅ Perftect state"
    elif score >= 4:
        verdict = "🟡 Descrete state"
    else:
        verdict = "❌ Critical state"

    return {"score": score, "verdict": verdict, "reasons": reasons}

if __name__ == "__main__":
    load_repos()  

choice = -1 

while (choice != 0):
    print("\n--- MENU ---")
    print("1. Add new repo")
    print("2. Analyze existing repos")
    print("0. Exit")

    try:
        choice = int(input("Choose an option: "))
    except ValueError:
        print("Please enter a valid number.")
        continue

    if choice == 0:
        print("Exiting")
    elif choice == 1:
        owner = input("Insert owner name: ")
        repo = input("Insert repo name: ")
        add_to_repoList(owner, repo)
        print("Repo added and saved!")

    elif choice == 2:
        if not repo_list:
            print("No repos found. Add some first.")
        else: 
            for repo in repo_list:
                meta = get_repo_metadata(repo.owner_name, repo.repo_name)
                freq = get_commit_frequency(repo.owner_name, repo.repo_name)
                contrib = get_contributors(repo.owner_name, repo.repo_name)

                print(f"\nRepo: {repo.owner_name}/{repo.repo_name}")
                print("Metadata:", meta)
                print("Commit frequency (per week):", freq)
                print("Contributors:", contrib)


                jsonString = [{"repo_owner":f"{repo.owner_name}" ,"repo_name":f"{repo.repo_name}", "data": meta, "frequqncy": freq, "contributors": contrib }]
                save_data_on_file(jsonString)
                
                semgrep_results = analyze_with_semgrep(repo.owner_name, repo.repo_name)
                if semgrep_results:
                    try:
                        semgrep_results_dict = json.loads(semgrep_results)
                        print(f"Semgrep findings: {len(semgrep_results_dict.get('results', []))} issues found")
                    except json.JSONDecodeError:
                        print("Errore: impossibile decodificare l'output di Semgrep")

                print(evaluate_repo(meta, freq, contrib,semgrep_results_dict) ) 



    else:
        print("Invalid choice")
