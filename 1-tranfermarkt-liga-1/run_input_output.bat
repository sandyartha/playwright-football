@echo off

for %%A IN (_input_to_output.py) do start /b /wait "" python "%%~fA"