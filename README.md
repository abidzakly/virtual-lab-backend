# Virtual-Lab-Backend
## How To
### Test Locally (or host and forward it with ngrok)
- Step 1: Open terminal (outside app folder). 
Type and Enter the following instructions below:
- Step 2: "python -m venv ***your virtual env name***".
- Step 3: ".\***your virtual env name***\Scripts\Activate".
- Step 4: "pip install fastapi uvicorn sqlalchemy pymysql".
- Step 5: Type "uvicorn vlabApp.main:app --reload".
- Done

### Go to http://127.0.0.1:8000/docs/ for Api Docs.
- You can also use Postman for testing.
## P.S.
- Make sure MySQL is turned on. (use xampp, laragon, any)
