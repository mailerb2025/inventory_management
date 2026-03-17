@echo off
echo ========================================
echo INVENTORY MANAGEMENT SYSTEM - TEST SUITE
echo ========================================
echo.

echo Step 1: Creating sample data...
python scripts/create_complete_sample_data.py
echo.

echo Step 2: Testing transactions...
python scripts/test_transactions.py
echo.

echo Step 3: Testing stock alerts...
python scripts/test_alerts.py
echo.

echo ========================================
echo ALL TESTS COMPLETED!
echo ========================================
echo.
echo You can now run the server:
echo python manage.py runserver
pause