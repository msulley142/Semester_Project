# Calibration 
Calibration is a personal growth and accountability tracker designed for individuals who struggle to build better habits, break bad ones,and develop new skills. With this web application, users can visually track their skill growth and habit progress over time.The ultimate goal of Calibration is to build a supportive community where people can grow, learn, and become the best version of themselves.

## Software Requirments 

Please download the following applications before installing the app.
Python 3.9+:https://www.python.org/downloads/
python pip:https://pypi.org/project/pip/
Docker:https://docs.docker.com/desktop/setup/install/windows-install/

## Installation
```bash
git clone https://github.com/msulley142/Semester_Project
cd  Semester_Poject/calibrationapp/
python manage.py makemigrations
python manage.py migrate 
docker compose up -d --build
```
Then open your browser and go to http://127.0.0.1:8000
Deployed website link: https://aircalibration.com/

## Getting Started 
1. Once you are on the landing page, click Sign Up.
2. After signing up, you will be directed to the dashboard.
3. From the dashboard, you can add new skills you’re learning (or want to learn in the future) and habits you want to make or break.
4. Log journal entries, set tasks, and complete them to earn XP, tokens, and unlock badges.
5. Track your growth visually through the Discipline Builder for now.


## License
The MIT License (MIT)

Copyright (c) Michael L. Sullivan

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.