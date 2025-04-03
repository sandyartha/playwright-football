@echo off

for %%A IN (_raw_to_output.py) do start /b /wait "" python "%%~fA"