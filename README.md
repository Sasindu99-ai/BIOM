# BIOM

# Get Started

1. Install Choco if not already installed:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```
2. Install Make if not already installed:
   ```powershell
   choco install make
   ```
3. Install uv if not already installed:
   ```powershell
   choco install uv
   ```
4. Clone this repository:
   ```powershell
   git clone https://github.com/Sasindu99-ai/BIOM.git
   ```
5. Navigate to the project directory:
   ```powershell
   cd BIOM
   ```
6. Open command prompt in the project directory and run:
   ```powershell
   make sync
   ```
7. After the sync is complete, run:
   ```powershell
   make run
   ```
