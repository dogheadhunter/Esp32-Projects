@echo off
echo Starting Iteration 2 validation...
echo This will take approximately 15-20 minutes
echo Output will be saved to iteration2_output.txt
echo.
echo DO NOT CLOSE THIS WINDOW
echo.

"c:\esp32-project\chatterbox_env\Scripts\python.exe" "c:\esp32-project\tools\tts-pipeline\run_iteration2.py" > "c:\esp32-project\tools\tts-pipeline\iteration2_output.txt" 2>&1

echo.
echo Iteration 2 complete!
echo Check iteration2_output.txt and validation_iteration2/ directory for results
pause
