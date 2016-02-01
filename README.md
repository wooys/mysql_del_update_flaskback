# mysql_del_update_flaskback
mysql闪回delete或update语句

该脚本:对delete或update误操作，利用mysqlbinlog转换binlog，分析出其中delete或update语句，做类似于flashback，还原回修改前的记录。

使用条件:
1. 高于5.1版本
2. 表结构中没有timestamp字段

注意:
1. 启用 binlog_format = row
2. binlog_row_image = full
3. 还原的指定目录的sql文件，可以根据需要修改
4. 闪回update语句之前，需要手工修改脚本中，具体表字段名，脚本第137行

例子:
脚本使用:
1. [root@vm2 tmp]# python parser_binlog_del_update_recovery.py 
Usage:python parser_binlog_del_update_recovery.py --help

2. [root@vm2 tmp]# python parser_binlog_del_update_recovery.py --help
usage: parser_binlog_del_update_recovery.py [-h] [-c COLNUM] [-t SQLTYPE]  [-f SQLFILE]

this script parser delete or update sql from binlog

optional arguments:
  -h, --help  show this help message and exit
  -c COLNUM   the number of table column
  -t SQLTYPE  input delete or update
  -f SQLFILE  sqlfile dir and sqlfile name from parser binlog
  --version   show program's version number and exit

3.  转储mysql-bin.xxxxxx
mysqlbinlog --base64-output=decode-rows -v -v  path/mysql-bin.xxxxxx > path/del/update_binlog.sql

4. del_binlog.sql
![del_binlog](https://cloud.githubusercontent.com/assets/16424025/12707465/d776b9e6-c8cf-11e5-9156-0cc97957129b.png)

5.recovery_del_result.sql
![recovery_del_result](https://cloud.githubusercontent.com/assets/16424025/12707610/4ba5278e-c8d1-11e5-9a63-5d6dcec1156f.png)

6.连接MySQLd，source path/recovery_del_result.sql; 即可还原误修改的数据。

7.update 语句，重复第3~5步，注意脚本中的参数

欢迎各位朋友指正，有无其他更好方案，谢谢!
