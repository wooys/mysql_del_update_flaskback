#!/usr/bin/env python
#encoding:utf-8
# scriptName:parser_binlog_del_update_recovery.py
# time:2016/1/29
# version:1.0
# email:mark5279@163.com
# author:Mark.Woo
# 这个脚本:误操作delete或update,通过从binlog,将其转换成反向语句
# 启用:binlog_format = row
# 适用如:delete from table [where table_column = ??] 或 update table set table_column = ?? where table_column = ??
# mysqlbinlog --base64-output=decode-rows --v -v mysql-bin.xxxxxxx [--start-position/start-datetime=x --stop-position/stop=datetime=x] > /path/mysql-bin.sql
# python parser_binlog_del_update_recovery.py --help
# 不适合:1.表结构中有timestamp字段; 2.低于MySQL5.5版本
# 注意:拉取update语句前，需要手工调整对应表字段的列表，第137行

import argparse
import sys
import re

parser = argparse.ArgumentParser(description = 'this script parser delete or update sql from binlog',)
parser.add_argument('-c', action='store', dest='colnum', help='the number of table column')
parser.add_argument('-t', action='store', dest='sqltype', help='input delete or update')
parser.add_argument('-f', action='store', dest='sqlfile', help='sqlfile dir and sqlfile name from parser binlog')
parser.add_argument('--version',action='version',version='%(prog)s 1.0')
args = parser.parse_args()

"""
print 'store = %r' %result.tabnum
print 'store = %r' %result.sqltype
print 'store = %r' %result.sqllogfile
"""

# 逆转binlog中delete语句
def div_delsql_list(sql_list,col_num):
    """ 把sql列表元素，按照INSERT INTO 语法结构合并到一起 """
    elem = []
    # 表列的数量col_num:col_num + 2
    col_num = int(col_num) + 2
    lens = len(sql_list)
    # lens/col_num:统计出列表中 INSERT INTO 组合数量
    for j in range(0,lens/col_num):
        """ 使用列表的分片方法 """
        sql= sql_list[(j*col_num):col_num*(j+1)]
        elem.append(sql)
    return elem 

def get_del_sql(file,col_num):
    sql = []
    with open(file) as f:
        for line in f: 
            if re.search('###',line):
                line = line.strip('\n').replace('### ','')
                line = re.sub("\@\d+\=",",",line.replace('DELETE FROM ','INSERT INTO ').replace("WHERE"," SELECT "))
                lines =  line.split('/*')[0]
                sql.append(lines)
    # 按照DELETE FROM分组
    result = div_delsql_list(sql,col_num)
    
    # 将最终结果,以;结尾,记录到/path/recovery.sql 文件，按照需要修改    
    with open('/tmp/recovery_del.sql','w') as f:
        for i in range(len(result)):
            row =  ''.join(result[i]).replace('SELECT   ,','SELECT ') + ";" + "\n"
            f.writelines(row)

# 逆转binlog中update语句
def div_sql_list(sql,col_tab,num_col):
    # elem 临时列表
    elem = []
    # lst_len 列表sql长度
    lst_len = len(sql)
    # 字段数量 + 6
    num_col = int(num_col) + 6 
    # 统计符合UPDATE语句数量
    n = (lst_len/num_col)
    for j in xrange(0,n):
        # 利用列表切片方法,组合每一条对应的UPDATE语句
        sqllist = sql[(j*num_col):(num_col*(j+1))]
        # elem列表保存
        elem.append(sqllist)
    # 返回列表给对应的函数
    return elem

def get_update_sql(sqlfile,col_tab,num_col):
    # 存放从sqlfile中解析出sql语句
    sql = list()
    # 使用with open原因,有自动关闭打开文件的功能
    with open(sqlfile) as f:
        for line in f:
            if re.search('###',line):
                line = re.sub('\(\d+\)','',line.strip('\n').replace('### ',''))
                line = line.strip()
                line = line.split('/*')[0]
                # 逆转UPDATE语句中,SET->WHERE, WHERE->SET
                if line == 'WHERE':
                    line = 'SET'
                elif line == 'SET':
                    line = 'WHERE'
                # 查询有带@num = val 字段
                if '@' in line:
                    # 获取@num中的num 序号
                    num = line.split('=')[0].replace('@','')
                    # 获取@num=val中的val 数据
                    val = line.split('=')[1]
                    # 将@num=val替换成col_name=val,col_tab表字段列表,col_tab[int(num)-1],利用num,取序号num对应的字段名称
                    line = col_tab[int(num)-1] + '=' + val
                # UPDATE语句存入sql列表中
                sql.append(line)
                    #print line
        #print sql

        # 将sql列表中元素,切分成符合一条UPDATE语法的sql语句,调用函数
        result = div_sql_list(sql,col_tab,num_col)
        #print result
        # 4个for循环作用,update set 后字段以逗号(,)连接,where 后字段以 and 连接
        for ml in range(len(result)):
            for idx in range(result[ml].index('SET')+1,result[ml].index('WHERE')-1):
                 result[ml][idx] = str(result[ml][idx]) + "," 
        for ml in range(len(result)):
            for idx in range(result[ml].index('WHERE')+1,len(result[ml])-1):
                 result[ml][idx] = str(result[ml][idx]) + " AND " 
        # 将result列表UPDATE语句,添加分号(;)结尾,保存到相应文件中,根据需要调整目录文件
        with open('/tmp/recovery_update.sql','w') as f:
            for bl in range(len(result)):
                row = ' '.join(result[bl]) + ";" + "\n"
                f.writelines(row)

if __name__=='__main__':
    if len(sys.argv) == 1:
        print 'Usage:python ' + sys.argv[0] + ' ' + '--help'
    elif args.sqltype == 'delete':
        print 'sql is doning ...'
        get_del_sql(args.sqlfile,args.colnum) 
        print 'function get_del_sql() convert delete into insert sql done!'
    elif args.sqltype == 'update':
        print 'sql is doning...'
        # 定义表字段的列表,修改手工修改
        col_tab=['id','col','gmt_time']
        get_update_sql(args.sqlfile,col_tab,args.colnum)
        print 'function get_update_sql convert update into old update sql done!'
