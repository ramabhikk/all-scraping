@Echo Off
for /F "usebackq tokens=1,2 delims==" %%i in (`wmic os get LocalDateTime /VALUE 2^>NUL`) do if '.%%i.'=='.LocalDateTime.' set ldt=%%j
set ldt=%ldt:~0,4%_%ldt:~4,2%_%ldt:~6,2%

CALL D:
CALL D:\Scrappers\vir\scripts\activate
CD "D:\Scrappers\Abhiram\TescoIE"
CALL scrapy crawl products -o Tesco_IE_%ldt%.csv
CALL deactivate
