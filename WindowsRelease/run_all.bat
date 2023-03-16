@echo off
set sum=0
for /f "delims= " %%a in ('robot -m maps/1.txt -c  ./SDK -f  "python main.py"') do ( set res1=%%a )
echo 1:%res1%
set /a sum=%sum%+%res1:~31,-2%

for /f "delims= " %%a in ('robot -m maps/2.txt -c  ./SDK -f  "python main.py"') do ( set res2=%%a )
echo 2:%res2%
set /a sum=%sum%+%res2:~31,-2%

for /f "delims= " %%a in ('robot -m maps/3.txt -c  ./SDK -f  "python main.py"') do ( set res3=%%a )
echo 3:%res3%
set sum=%sum%+%res3:~31,-2%

for /f "delims= " %%a in ('robot -m maps/4.txt -c  ./SDK -f  "python main.py"') do ( set res4=%%a )
echo 4:%res4%
set /a sum=%sum%+%res4:~31,-2%

echo result: %sum%