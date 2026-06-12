# MephistDataKit
`MephistDataKit` - a set of utilities for remote access and analysis of the plasma discharge database of the MEPhIST (MEPhI Spherical Tokamak). It can work via the Internet using personal login credentials for the portal [**tokamak.mephi.ru**](https://tokamak.mephi.ru).

## 🎯 Project Description
MephistDataKit is a Python package for working with HDF5/NeXuS files of the MEPhIST tokamak. It provides:

1.  **Remote Data Access**: A client based on **[requests](https://pypi.org/project/requests/)** for interacting with the REST API of the tokamak data storage via personal access tokens generated on the portal [**tokamak.mephi.ru**](https://tokamak.mephi.ru).
2.  **Automatic Caching**: Upon the first request for a discharge file, it is saved locally to minimize server load and speed up data processing. The cache volume can be configured, and caching can be disabled entirely.
3.  **Data Processing**: A library of regularly updated methods for analyzing tokamak signals (plasma current, interferometry, etc.), based on the developments of laboratory staff.
4.  **Extensibility**: The ability for students and graduate students to upgrade and add new processing methods and examples into a single ecosystem using Git tools.

The repository actually has two main goals:
*   To provide direct remote access to data for many users with the ability to utilize local computational resources for processing. Firstly, to reduce the load on web services, and secondly, to enable working with big data, which is difficult to implement on the used JupyterLab server.
*   To become the main source of up-to-date data processing methods. For example, if coefficients for calculating plasma current change, the author can make a pull request. Firstly, Git will ensure the preservation of change history, and secondly, it will allow operational distribution of updates among users and automatic implementation (CI/CD) of changes into data collection and processing scripts (HDF5 packagers, graph generators on the web portal, etc.).

## 📋 Requirements
1.  **[Python 3.12+](https://www.python.org/downloads/)** - programming language
2.  **[VS Code](https://code.visualstudio.com/)** - universal development environment (IDE)
3.  **[uv](https://github.com/astral-sh/uv)** - package and environment manager
4.  **[Git](https://git-scm.com/)** - version control system

## 🏁 Quick Start
### 1. Follow the instructions from the `🚀 Installation` section (presented below)
### 2. Configuration Setup
Copy the file `config_example.yaml` and rename it to `config.yaml`. Do not use the file `config_example.yaml`, as it is indexed in Git, which could compromise your personal access token. Also, by default, the client looks for configuration in a file named `config.yaml` in the project root directory. Insert the access token obtained according to the instructions from the `🔑 Getting API Access` section (presented below) into the `api_token` field. For now, the rest of the settings can be left as default.

Also, when working with a large number of pulses, when warnings about the lack of certain diagnostics in the database may often arise in the terminal, it might be convenient to disable some warnings using the `show_progress` and `console_level` settings. With the `ERROR` variant, only errors are displayed; with `WARNING` - errors and warnings; with `INFO` - all messages (makes sense for debugging). At the same time, the `show_progress` setting works independently.

```yaml
# Mephist API Client Configuration
# Connection Settings
server:
  base_url: "https://tokamak.mephi.ru/"
  base_path: "/orders/shots-api/"
  verify_ssl: true                  # for self-signed certificates
# Authentication REPLACE TOKEN WITH YOURS
auth:
  api_token: "your_personal_token"
# Data Download Settings
download:
  chunk_size: 8192                  # Chunk size for downloading
  timeout: 5                        # Request timeout (seconds)
  retry_attempts: 3                 # Number of retry attempts on error
  show_progress: true               # Enable/disable progress bar
# Data Caching Settings
cache:
  use_cache: true                   # Use cache by default (otherwise it will download from server every time)
  cache_dir: "./.cache"             # directory for storing cache (Created automatically)
  cache_max: "3 GB"                 # Maximum cache size in format "500 MB", "1GB", "100KB" and "0" to disable limit
logging:
  console_level: "INFO"             # Console message output level: ERROR, WARNING, INFO
  verbose_stats: true               # output detailed information for server statistics
```

> **Important:** Replace `your_personal_token` with the token obtained on the tokamak portal.

### 3. First Launch
1.  **Open the project** in VS Code: `File → Open Folder → select MephistDataKit`
2.  **Select Interpreter**:
    *   Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
    *   Select `Python: Select Interpreter`
    *   Select `mephistdatakit` from your project (if you installed dependencies in the virtual env venv) or standard Python, if via pip.
3.  Copy files from the `examples` directory to the `workdir` directory.
4.  Open any copied example from workdir.
5.  Run the script directly from VS Code right-click → "Run Python File", or the button in the form of an inverted triangle in the top right corner.
6.  You are successful.

## 🚀 Installation
### Method 1: Via uv (recommended)
#### 1. Install programs from links in the `📋 Requirements` section. Installation of the latest versions is recommended.
#### 2. Get an instance of the MephistDataKit package. For this:
#### 2.1 Open a terminal (Terminal/PowerShell) in any directory where you want to install the package. To do this, right-click in the desired directory -> `Open in Terminal` (or `git bash here`, or press right mouse button on File button in the left top corner of file manager and press `Open in Powershell`)..
#### 2.2 If you are working via the portal tokamak.mephi.ru:
*   Open the Git repository hosting service **[tokamak.mephi.ru/git](https://tokamak.mephi.ru/git/explore/repos)**
*   Go to personal settings (button in the top right corner => Settings)
*   Create a password in the `Account` section or create an application password in the `Applications` section
*   Execute the command `git clone https://tokamak.mephi.ru/git/mephist0/MephistDataKit.git` in the previously opened terminal
*   In the terminal, you will first be asked for a login (same as on the portal tokamak.mephi.ru) and then the password you created in the previous step. Note that for security reasons, when entering the password, git does not display it in the terminal window, but the password is nevertheless entered. After entering the login and password, press Enter to confirm.
#### 2.3 If for some reason you do not want to use Git, you can get an instance of the repository as a ZIP archive via **[this](https://tokamak.mephi.ru/git/mephist0/MephistDataKit/archive/main.zip)** link or on the website **[tokamak.mephi.ru/git](https://tokamak.mephi.ru/git/explore/repos)**
#### 3 To move to the root directory of the repository, execute the command `cd MephistDataKit`, if downloaded via git, or unpack the ZIP archive and open the terminal in the MephistDataKit directory, if downloaded from the site.
#### 4. Create and activate the virtual environment. To do this, execute the command `uv sync` in the MephistDataKit directory. Wait until all dependencies are downloaded and assembled. Note: recently there may be problems downloading some dependencies from Russia. You may need to enable VPN.

### Method 2: Via pip (without virtual environment)
1.  Execute points 1 - 3 from the previous section for installation via uv.
2.  Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

## Working in VS Code
For convenient work in VS Code:
1.  In the left vertical menu, open the `Extensions` tab and install:
    *   Python
    *   Pylance
    *   Python Environments
    *   Python Extension Pack
    *   Git Extension Pack
    *   Jupyter
    Install dependencies via uv or pip according to the instructions above.
    Restart VS Code.
2.  **Open the project** in VS Code: `File → Open Folder → find and select MephistDataKit`
3.  **Select Interpreter**:
    *   Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
    *   Select `Python: Select Interpreter`
    *   Select `mephistdatakit` from your project (if you installed dependencies in the virtual env venv) or standard Python, if you installed dependencies via pip.

Now you can run scripts directly from VS Code right-click → "Run Python File", or the button in the form of an inverted triangle in the top right corner.

## 🔑 Getting API Access
To work with tokamak data via the Internet, you need to obtain a personal access token, which is a sequence of 60 characters. To do this:
1.  **Request a registration link** from laboratory staff or by email `tokamak@mephi.ru` to create login credentials for the portal.
2.  **Log in to the portal** [**tokamak.mephi.ru**](https://tokamak.mephi.ru) using the obtained login/password.
3.  After successful authorization, **go to the [personal settings page](https://tokamak.mephi.ru:8443/if/user/#/settings)**. 
4.  **Open the section** `Tokens and Applications`
5.  **Click the button** `Create Token` and assign it an arbitrary name (without Cyrillic!)
6.  In the appearing tab `Actions`, click `Copy Token` and paste it into the `config.yaml` file, which you must create yourself based on the template (see example below or in the file `config_example.yaml`).
7.  Do not share your token with anyone and do not store it on public resources. In case of compromise, delete the token on the **[personal settings page](https://tokamak.mephi.ru:8443/if/user/#/settings)** and create a new one.

Note that tokens from users with "Administrator" status are not accepted!

## 📁 Project Structure
Note that the `examples` directory is not intended for work. Use the `workdir` directory for personal scripts, as it is not indexed in Git. Editing files in other directories makes sense only if you plan to make a `pull request`.

```text
MephistDataKit/
├── src/                         # Package source code
│   └── mephistdatakit/          # Main package
│       ├── __init__.py          # Package initialization
│       ├── config.py            # Import configurations from config.yaml
│       ├── common.py            # common data processing methods
│       ├── mw_interferometry.py # microwave interferometry data processing
│       ├── client.py            # Client for API work
│       └── shot.py              # getting plasma parameters from HDF5 file
├── examples/                    # Usage examples
│   ├── general_chart.ipynb
│   ├── connection_and_download_test.ipynb
|   ├── statistics_charts.ipynb
|   ├── ...
│   └── data.py
├── .vscode                     # Settings for correct library display in VS Code
├── workdir/                    # Working directory for users
├── .cache/                     # Cache of downloaded files
├── docs/                       # Auto-documentation based on pdoc
├── config.yaml                 # Configuration file (YOU MUST CREATE IT!)
├── config_example.yaml         # Example configuration file
├── pyproject.toml              # Project configuration for uv
├── requirements.txt            # List of python dependencies
├── .gitignore                  # List of directories and files to ignore in Git
└── README.md                   # This documentation
```

## 📦 Main Modules
### mephistdatakit.client
Module for interacting with the MEPhIST tokamak API. The main class is `Client`. Provides methods for authentication, getting a list of shots, downloading data, and working with cache.

### mephistdatakit.shot
Module for processing and analyzing tokamak data. The main class is `Shot`. Contains functions for:
- Calculating plasma current from Rogowski coil data
- Processing interferometry data for measuring electron density
- Working with MEPhIST tokamak HDF5 files
- and much more

## 📝 Usage Examples
### Example 1: Checking connection to server and token validity
```python
import mephistdatakit as mdk
# Create client application object with token specified in config.yaml file
client = mdk.Client()
# In principle you can specify the config file name, but keep in mind it won't be in .gitignore
client = mdk.Client("my_config.yaml")
# Check connection to server (Optional)
client.test_connection()
# Check authentication (Optional, it repeats on every file request)
client.authenticate()
# Get list with list of shots in int list
shots_list = client.get_shots_list()
print(shots_list)
```

### Example 2: Downloading data from server
```python
import mephistdatakit as mdk
client = mdk.Client()
for shot_id in shots_list[shots_list.index(3063):shots_list.index(3063)+4]:
    hdf5_file = client.get_shot(shot_id)
    shot = mdk.Shot(hdf5_file)
    try:
        time, plasma_current = shot.get_plasma_current()
        time, plasma_density = shot.get_plasma_density()
        print(f"STATISTICS: shot {shot_id}   {shot.get_gas()} {shot.get_pressure():.2e} mBar  {max(plasma_current):.2f} kA {max(plasma_density):.1e} m^2")
    except:
        pass
```

### Example 3: Working with cache
```python
import mephistdatakit as mdk
# Create client application object with token specified in config.yaml file
client = mdk.Client()
cache_info = client.cache_info()
print(f"Files in cache: {cache_info['files_count']}")
print(f"Cache size: {cache_info['total_size_mb']:.2f} MB")
client.cache_management("cleanup")
# nothing was actually deleted, as cache volume is less than cache_max parameter in config.yaml
cache_info = client.cache_info()
print(f"Files in cache: {cache_info['files_count']}")
print(f"Cache size: {cache_info['total_size_mb']:.2f} MB")
client.cache_management("clear")
# Now the cache is empty
cache_info = client.cache_info()
print(f"Files in cache: {cache_info['files_count']}")
print(f"Cache size: {cache_info['total_size_mb']:.2f} MB")
```

You can find more examples in the `examples/` directory.

## 📚 Method Documentation
Method documentation is implemented as Docstrings. Auto-generation of documentation for the `mephistdatakit` package is based on the **[pdoc](https://pdoc.dev/)** package. To view it, open the file **[/docs/index.html](/docs/index.html)** in a browser.

When making changes to the package, update the documentation with the command:
```bash
pdoc ./src/mephistdatakit -o ./docs
```
Important: The command works only when the virtual environment `mephistdatakit` is active, as during execution it analyzes the entire package and imports all methods.

## 🤝 Development
### Adding new methods
1.  **Create a new file** in `src/mephistdatakit/` or add a function to an existing module.
2.  **Add documentation** in docstring format with description of parameters, return values, and usage examples.
3.  **Test the work** on real data.
4.  **Generate documentation** using pdoc.
5.  **Make a pull request** to the main repository.

### Structure of a new function
```python
def new_processing_method(data, param1, param2=default):
    """
    Brief function description.
    Parameters
    ----------
    data : np.ndarray
    Description of input data
    param1 : float
    Description of first parameter
    param2 : str, optional
    Description of second parameter (default: default)
    Returns
    -------
    result : np.ndarray
    Description of return value
    Examples
    --------
    >>> result = new_processing_method(data, 10.5)
    >>> print(result.shape)
    """
    # Function implementation
    return processed_data
```

## 📧 Support
-   **Technical questions and data access**: **tokamak@mephi.ru**
-   **Questions on framework usage**: create issues in the project repository
-   **Suggestions for improvement**: pull requests are welcome

## 📄 License
You can review the license on the file storage via the link: **[tokamak.mephi.ru/license](https://tokamak.mephi.ru/license)**
The license for this repository is not yet formalized.