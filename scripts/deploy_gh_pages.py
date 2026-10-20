import subprocess
import os
import shutil
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def run(cmd):
    print(">>", cmd)
    res = subprocess.run(cmd, shell=True, cwd=str(BASE), capture_output=True, encoding="utf-8", errors="replace")
    if res.returncode != 0 and res.stderr:
        print("STDERR:", res.stderr.strip()[:300])
    if res.stdout and res.stdout.strip():
        print("STDOUT:", res.stdout.strip()[:300])
    return res

def main():
    print("[*] Staging site build in temporary directory...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # 1. Copy web/* to tmp_path
        web_dir = BASE / "web"
        for item in web_dir.iterdir():
            if item.name == ".git":
                continue
            target = tmp_path / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(target), dirs_exist_ok=True)
            else:
                shutil.copy2(str(item), str(target))

        # 2. Also preserve web/ subdirectory
        web_sub = tmp_path / "web"
        web_sub.mkdir(exist_ok=True)
        for item in web_dir.iterdir():
            if item.name == ".git":
                continue
            target = web_sub / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(target), dirs_exist_ok=True)
            else:
                shutil.copy2(str(item), str(target))

        # 3. Copy workflows to tmp_path / workflows
        print("[*] Staging workflows directory...")
        shutil.copytree(str(BASE / "workflows"), str(tmp_path / "workflows"), dirs_exist_ok=True)

        # 4. Write .nojekyll
        (tmp_path / ".nojekyll").write_text("# Disable Jekyll on GitHub Pages\n", encoding="utf-8")
        (web_sub / ".nojekyll").write_text("# Disable Jekyll on GitHub Pages\n", encoding="utf-8")

        print("[*] Switching to orphan gh-pages branch...")
        run("git branch -D gh-pages")
        run("git checkout --orphan gh-pages")
        run("git rm -rf .")

        print("[*] Populating gh-pages from staged build...")
        for item in tmp_path.iterdir():
            target = BASE / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(target), dirs_exist_ok=True)
            else:
                shutil.copy2(str(item), str(target))

        print("[*] Committing and pushing gh-pages...")
        run("git add -A")
        run('git commit -m "publish site to gh-pages"')
        res = run("git push origin gh-pages --force")

        print("[*] Restoring main branch...")
        run("git checkout -f main")

        if res.returncode == 0:
            print("[+] SUCCESS: gh-pages branch published to GitHub!")
        else:
            print("[-] Notice during push (check above)")

if __name__ == "__main__":
    main()
