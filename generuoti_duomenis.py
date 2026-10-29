"""Sugeneruoja 4 PAVYZDINIUS (išgalvotus) duomenų rinkinius aplanke duomenys/.
Mastai (pajamos, darbuotojai, atlyginimai, pelningumas) pagal viešus sektoriaus duomenis,
mėnesio transakcijos – sumodeliuotos. Paleidimas: python generuoti_duomenis.py"""
import os
os.makedirs("duomenys",exist_ok=True)
import random,json,csv,datetime as dt,openpyxl
from openpyxl.styles import Font,PatternFill
M=['2025-11','2025-12','2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07','2026-08','2026-09','2026-10']
def due(d,days): return (dt.date.fromisoformat(d)+dt.timedelta(days=days)).isoformat()
TODAY=dt.date(2026,10,29)
def add(rows,d,k,cat,pad,s,vat=0.21,term=30,paid=None):
    s=round(s,2);v=round(abs(s)*vat,2)*(1 if s>0 else -1);md=due(d,term)
    if paid is None: paid='Taip' if dt.date.fromisoformat(md)<=TODAY else 'Ne'
    rows.append([d,k,cat,pad,s,v,md,paid])

NOTE='Išgalvota įmonė, mastai pagal viešus sektoriaus duomenis; mėnesio transakcijos sumodeliuotos.'
def W(n,w): return n*w*1.0177
def manuf():
    r=random.Random(1);rows=[];sea=[0.85,0.6,0.55,0.65,0.9,1.1,1.2,1.25,1.2,1.15,1.1,0.95]
    cl=[('Statybų grupė „Akmena“ (pavyzdys)',.32,60),('UAB Fasadų meistrai (pavyzdys)',.22,45),('Statybinių prekių tinklas (pavyzdys)',.26,30),('Kiti klientai',.20,30)]
    for i,m in enumerate(M):
        rev=401_000*sea[i]/0.958
        for k,(c,sh,t) in enumerate(cl):
            paid='Ne' if (c.startswith('Statybų grupė') and m in('2026-07','2026-08')) else None
            add(rows,f'{m}-{5+k*6:02d}',c,'Pardavimai',['Sausieji mišiniai','Klijai ir hidroizoliacija'][k%2],rev*sh*(0.96+0.08*r.random()),.21,t,paid)
        mat=rev*(0.555 if i<5 else 0.625)
        add(rows,f'{m}-07','Cemento ir chemijos tiekėjas (pavyzdys)','Žaliavos ir medžiagos','Sausieji mišiniai',-mat*.6,term=30)
        add(rows,f'{m}-09','Polimerų tiekėjas (pavyzdys)','Žaliavos ir medžiagos','Klijai ir hidroizoliacija',-mat*.4,term=30)
        add(rows,f'{m}-10','Darbuotojai (24 žm.)','Darbo užmokestis','Sausieji mišiniai',-W(24,2991),0,0)
        add(rows,f'{m}-12','Energijos tiekėjas','Energija','Sausieji mišiniai',-16000*(1.3 if i in(1,2,3) else 1),term=20)
        add(rows,f'{m}-15','Transporto partneris (pavyzdys)','Logistika','Klijai ir hidroizoliacija',-rev*0.06,term=30)
        add(rows,f'{m}-01','Gamybos patalpų nuoma','Nuoma','Sausieji mišiniai',-14000,term=0)
        add(rows,f'{m}-18','Administracija, IT, draudimas','Administracinės sąnaudos','Klijai ir hidroizoliacija',-31800,term=15)
        add(rows,f'{m}-20','Reklama ir parodos','Marketingas','Klijai ir hidroizoliacija',-4000,term=30)
    return dict(id='gamyba',name='UAB „Nerio mišiniai“ (išgalvota) · statybinių mišinių gamintojas, ~4,8 M€, 24 darb.',opening=700_000,rows=rows,
      story='Žaliavų (cemento, polimerų) brangimas nuo 2026-04 numušė maržą ~7 p.p. ir metai baigiasi nedideliu nuostoliu; didžiausias klientas vėluoja apmokėti 2 sąskaitas; žiemą sezoninis pajamų kritimas.')
def agri():
    r=random.Random(2);rows=[];sea=[1.25,0.6,0.45,0.45,0.55,0.6,0.6,0.7,1.1,2.0,1.9,1.6]
    cl=[('Grūdų supirkėjas „Agro Baltic“ (pavyzdys)',.45,30),('Pieno perdirbėjas (pavyzdys)',.25,30),('Grūdų eksportuotojas (pavyzdys)',.2,45)]
    for i,m in enumerate(M):
        rev=715_000*sea[i]/1.0
        for k,(c,sh,t) in enumerate(cl):
            paid='Ne' if c.startswith('Grūdų eksportuotojas') and m in('2026-08','2026-09') else None
            add(rows,f'{m}-{6+k*7:02d}',c,'Produkcijos pardavimai',['Augalininkystė','Gyvulininkystė','Augalininkystė'][k],rev*sh*(0.96+0.08*r.random()),.21 if k<2 else 0,t,paid)
        add(rows,f'{m}-28','Nacionalinė mokėjimo agentūra','ES tiesioginės išmokos','Augalininkystė',715_000*0.12,0,0)
        inp=[0.02,0.02,0.05,0.12,0.2,0.22,0.15,0.06,0.04,0.05,0.05,0.02][i]*8_582_000*0.30*(1.15 if i>=3 and i<=6 else 1)
        add(rows,f'{m}-09','Trąšų ir sėklų tiekėjas (pavyzdys)','Trąšos, sėklos, augalų apsauga','Augalininkystė',-inp,term=60)
        add(rows,f'{m}-11','Pašarų tiekėjas (pavyzdys)','Pašarai','Gyvulininkystė',-715_000*0.08,term=30)
        add(rows,f'{m}-10','Darbuotojai (69 žm.)','Darbo užmokestis','Augalininkystė',-W(69,1950),0,0)
        add(rows,f'{m}-13','Degalų tiekėjas (pavyzdys)','Degalai','Augalininkystė',-715_000*0.06*(1.6 if i in(5,6,9,10) else 0.8),term=14)
        add(rows,f'{m}-15','Žemės savininkai','Žemės nuoma','Augalininkystė',-50000,0,0)
        add(rows,f'{m}-17','Technikos lizingas (pavyzdys)','Technikos lizingas ir remontas','Augalininkystė',-62000,0,0)
        add(rows,f'{m}-20','Veterinarija, draudimas, administracija','Administracinės sąnaudos','Gyvulininkystė',-14000,term=15)
        if m=='2026-05': add(rows,f'{m}-20','Kombaino pardavėjas (pavyzdys)','Investicijos (technika)','Augalininkystė',-420000,term=0)
    return dict(id='zemes_ukis',name='ŽŪB „Lygumų ūkis“ (išgalvota) · žemės ūkio bendrovė, ~8,6 M€, 69 darb.',opening=1_250_000,rows=rows,
      story='Labai sezoninis verslas: pavasarį perkamos brangesnės trąšos ir sėklos, o grūdų pajamos ateina rugsėjį–lapkritį – vasarą susidaro pinigų tarpas; grūdų eksportuotojas vėluoja apmokėti.')
def tech():
    r=random.Random(3);rows=[];rows_=[]
    for i,m in enumerate(M):
        rev=95_000+i*11_500;emp=10+i//2 if i<10 else 15
        cl=[('Logistikos centras „Šiaurės sandėliai“ (pavyzdys)',.4,60),('Prekybos tinklas (pavyzdys)',.35,30),('Pilotiniai klientai (ES)',.25,30)]
        for k,(c,sh,t) in enumerate(cl):
            paid='Ne' if c.startswith('Logistikos centras') and m in('2026-08','2026-09') else None
            add(rows,f'{m}-{5+k*8:02d}',c,'Pardavimai (robotai ir SaaS)',['Robotų pardavimai','SaaS prenumeratos','Robotų pardavimai'][k],rev*sh*(0.95+0.1*r.random()),.21 if k<2 else 0,t,paid)
        add(rows,f'{m}-08','Komponentų tiekėjas (pavyzdys)','Komponentai ir aparatūra','Robotų pardavimai',-rev*0.27,term=30)
        add(rows,f'{m}-10',f'Darbuotojai ({emp} žm.)','Darbo užmokestis','Robotų pardavimai',-W(emp,5428)*0.93,0,0)
        add(rows,f'{m}-14','Debesų paslaugos','IT ir debesija','SaaS prenumeratos',-rev*0.04,term=30)
        add(rows,f'{m}-01','Biuro ir dirbtuvių nuoma','Nuoma','Robotų pardavimai',-6500,term=0)
        add(rows,f'{m}-18','Komandiruotės ir parodos','Pardavimų sąnaudos','Robotų pardavimai',-rev*0.04,term=15)
        add(rows,f'{m}-24','R&D subrangovai (pavyzdys)','Subranga (R&D)','Robotų pardavimai',-26000,term=30)
        add(rows,f'{m}-22','Teisinės, apskaitos paslaugos','Administracinės sąnaudos','SaaS prenumeratos',-5200,term=15)
    return dict(id='technologijos',name='UAB „Robotikos sprendimai“ (išgalvota) · logistikos robotai ir SaaS, ~1,9 M€, 14 darb.',opening=650_000,rows=rows,
      story='Sparti augimo trajektorija (pajamos per metus ~2,3 karto), bet nauji darbuotojai ir komponentai suvalgo pinigus – veikla apie lūžio tašką; didžiausias klientas vėluoja ~125 k€.')
def group():
    r=random.Random(4);rows=[]
    for i,m in enumerate(M):
        s=[0.8,0.65,0.5,0.55,0.75,1.0,1.1,1.2,1.25,1.2,1.1,0.9][i]
        add(rows,f'{m}-15','Butų pirkėjai','Butų pardavimai','Šiaurės plėtra UAB',1_300_000*s,.21,0)
        add(rows,f'{m}-25','Instituciniai investuotojai (pavyzdys)','Pardavimai','Šiaurės plėtra UAB',350_000*s,.21,60,'Ne' if m in('2026-07','2026-08') else None)
        add(rows,f'{m}-08','Statybos rangovas (pavyzdys)','Statybos ir medžiagos','Šiaurės plėtra UAB',-1_650_000*s*(0.90 if i<6 else 1.06),term=30)
        add(rows,f'{m}-12','Pardavimai ir marketingas','Marketingas','Šiaurės plėtra UAB',-38000,term=30)
        add(rows,f'{m}-05','Užsakovai','Statybos darbai','Šiaurės statyba UAB',560_000*s,.21,45)
        add(rows,f'{m}-09','Medžiagų tiekėjas (pavyzdys)','Statybos ir medžiagos','Šiaurės statyba UAB',-560_000*s*(0.83 if i<6 else 0.95),term=30)
        add(rows,f'{m}-10','Darbuotojai (48 žm.)','Darbo užmokestis','Šiaurės statyba UAB',-W(48,2500),0,0)
        add(rows,f'{m}-01','Nuomininkai','Nuomos pajamos','Šiaurės nuoma UAB',330_000,.21,10)
        add(rows,f'{m}-12','Pastatų priežiūra','Priežiūra','Šiaurės nuoma UAB',-70_000,term=30)
        add(rows,f'{m}-20','Bankas','Palūkanos','Šiaurės nuoma UAB',-260_000,0,0)
        add(rows,f'{m}-25','Bankas (paskola)','Paskolos įmokos','Šiaurės nuoma UAB',-120_000,0,0)
        add(rows,f'{m}-28','Grupės valdymas (4 darb.)','Administracinės sąnaudos','Šiaurės grupė UAB (valdymas)',-70_000,term=0)
    return dict(id='grupe',name='„Šiaurės grupė“ (išgalvota) · NT grupė su 3 dukterinėmis, ~28 M€ konsoliduotai',opening=5_600_000,rows=rows,
      story='Statybos kainų augimas nuo 2026-05 numušė plėtros maržą, palūkanų našta ~3,1 M€ – grupė metus baigia ~2 M€ nuostoliu; investuotojas vėluoja apmokėti ~0,7 M€.')
H=['data','kontrahentas','kategorija','padalinys','suma','PVM','mokejimo_terminas','apmoketa']
out=[]
for f in (manuf,agri,tech,group):
    d=f();out.append(d);fn='duomenys/pavyzdys_'+d['id']
    with open(fn+'.csv','w',newline='',encoding='utf-8-sig') as fh:
        w=csv.writer(fh);w.writerow(H);w.writerows(d['rows'])
    wb=openpyxl.Workbook();ws=wb.active;ws.title='Transakcijos';ws.append(H)
    for c in ws[1]: c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='1D4ED8')
    for row in d['rows']: ws.append(row)
    for col,wd in zip('ABCDEFGH',[12,36,26,26,14,12,16,10]): ws.column_dimensions[col].width=wd
    n=wb.create_sheet('Apie');n.append(['PAVYZDINIAI DUOMENYS. '+NOTE]);n.append([d['name']]);n.append([d['story']]);n.append(['suma: + pajamos, − išlaidos (EUR be PVM)'])
    wb.save(fn+'.xlsx');rv=sum(x[4] for x in d['rows'] if x[4]>0);pl=sum(x[4] for x in d['rows'] if 'Paskol' not in x[2] and 'Investic' not in x[2]);print(fn,len(d['rows']),round(rv/1e6,2),'M€ rezultatas',round(pl/1e3),'k€',round(pl/rv*100,1),'%')
json.dump([{k:v for k,v in d.items() if k!='rows'} for d in out],open('duomenys/rinkiniai.json','w'),ensure_ascii=False,indent=1)
