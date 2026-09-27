import json
W=json.load(open('words.json'))
# so tu hien thi cua moi cue (theo DISPLAY trong render.py)
EN=["The dogs ran straight for the tanks...","just as they were trained.","But these were Soviet dogs.","And so were the tanks.","1941.",
"German tanks were tearing into the Soviet Union.","For years, trainers kept the dogs hungry,","and hid their food under tanks.","A tank meant dinner.",
"Now each dog wore explosives, with a wooden lever on its back.","Under a tank, the lever hit the steel.","But they had trained on Soviet tanks:",
"silent, still, smelling of diesel.","German tanks roared, fired, and smelled strange.","Some dogs ran for the tanks they knew.",
"Of the first 30 dogs, only 4 reached a German tank.","Others fled back to their own trenches...","still carrying their bombs.",
"Moscow later claimed 300 tanks.","Historians doubt it.","Because out there, in the smoke and noise,","hungry and terrified..."]
T={
'es':["Los perros corrieron directo hacia los tanques...","tal como los habían entrenado.","Pero eran perros soviéticos.","Y los tanques también.","1941.",
"Los tanques alemanes avanzaban sobre la Unión Soviética.","Durante años, los adiestradores mantuvieron a los perros con hambre,","y escondían su comida bajo los tanques.","Un tanque significaba comida.",
"Ahora cada perro llevaba explosivos, con una palanca de madera en el lomo.","Bajo un tanque, la palanca golpeaba el acero.","Pero se habían entrenado con tanques soviéticos:",
"silenciosos, inmóviles, con olor a diésel.","Los tanques alemanes rugían, disparaban y olían extraño.","Algunos perros corrieron hacia los tanques que conocían.",
"De los primeros 30 perros, solo 4 alcanzaron un tanque alemán.","Otros huyeron de vuelta a sus propias trincheras...","todavía cargando sus bombas.",
"Moscú afirmó después 300 tanques.","Los historiadores lo dudan.","Porque allí, entre el humo y el ruido,","hambrientos y aterrados..."],
'pt':["Os cães correram direto para os tanques...","exatamente como foram treinados.","Mas eram cães soviéticos.","E os tanques também.","1941.",
"Tanques alemães avançavam sobre a União Soviética.","Por anos, os treinadores mantiveram os cães famintos,","e escondiam a comida deles sob tanques.","Um tanque significava comida.",
"Agora cada cão carregava explosivos, com uma alavanca de madeira nas costas.","Sob um tanque, a alavanca batia no aço.","Mas eles treinaram com tanques soviéticos:",
"silenciosos, parados, com cheiro de diesel.","Os tanques alemães rugiam, disparavam e tinham um cheiro estranho.","Alguns cães correram para os tanques que conheciam.",
"Dos primeiros 30 cães, só 4 chegaram a um tanque alemão.","Outros fugiram de volta às próprias trincheiras...","ainda carregando suas bombas.",
"Moscou depois alegou 300 tanques.","Os historiadores duvidam.","Porque lá fora, na fumaça e no barulho,","famintos e apavorados..."],
'de':["Die Hunde rannten direkt auf die Panzer zu...","genau wie man es ihnen beigebracht hatte.","Aber es waren sowjetische Hunde.","Und auch die Panzer waren sowjetisch.","1941.",
"Deutsche Panzer drangen in die Sowjetunion ein.","Jahrelang hielten Ausbilder die Hunde hungrig","und versteckten ihr Futter unter Panzern.","Ein Panzer bedeutete Futter.",
"Nun trug jeder Hund Sprengstoff, mit einem Holzhebel auf dem Rücken.","Unter einem Panzer traf der Hebel auf den Stahl.","Doch sie hatten mit sowjetischen Panzern geübt:",
"still, reglos, mit Dieselgeruch.","Deutsche Panzer dröhnten, feuerten und rochen fremd.","Manche Hunde liefen zu den Panzern, die sie kannten.",
"Von den ersten 30 Hunden erreichten nur 4 einen deutschen Panzer.","Andere flohen zurück in die eigenen Schützengräben...","noch immer mit ihren Bomben.",
"Moskau behauptete später: 300 Panzer.","Historiker bezweifeln das.","Denn dort draußen, in Rauch und Lärm,","hungrig und verängstigt..."],
'fr':["Les chiens ont foncé droit sur les chars...","exactement comme on le leur avait appris.","Mais c'étaient des chiens soviétiques.","Et les chars aussi.","1941.",
"Les chars allemands déferlaient sur l'Union soviétique.","Pendant des années, les dresseurs ont affamé les chiens,","et caché leur nourriture sous des chars.","Un char, c'était le repas.",
"Désormais, chaque chien portait des explosifs, avec un levier en bois sur le dos.","Sous un char, le levier heurtait l'acier.","Mais ils s'étaient entraînés sur des chars soviétiques :",
"silencieux, immobiles, sentant le diesel.","Les chars allemands rugissaient, tiraient, et avaient une odeur étrange.","Certains chiens ont couru vers les chars qu'ils connaissaient.",
"Sur les 30 premiers chiens, seuls 4 ont atteint un char allemand.","D'autres se sont enfuis vers leurs propres tranchées...","toujours chargés de leurs bombes.",
"Moscou a ensuite revendiqué 300 chars.","Les historiens en doutent.","Car là-bas, dans la fumée et le bruit,","affamés et terrifiés..."]}
cues=[];k=0
for s in EN:
    n=len(s.split()); ws=W[k:k+n]
    assert ' '.join(w[0] for w in ws)==s,(s,[w[0] for w in ws]); cues.append([ws[0][1],ws[-1][2]]); k+=n
assert k==len(W)
for i in range(len(cues)):
    nxt=cues[i+1][0] if i+1<len(cues) else 54.1
    cues[i][1]=min(nxt-0.02, cues[i][1]+0.35)
def ts(x):
    ms=int(round(x*1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
for lang,lines in [('en',EN)]+list(T.items()):
    assert len(lines)==len(cues)
    with open(f'../upload/log011_subtitles_{lang}.srt','w',encoding='utf-8') as f:
        for i,(c,l) in enumerate(zip(cues,lines)):
            f.write(f"{i+1}\n{ts(c[0])} --> {ts(c[1])}\n{l}\n\n")
print(open('../upload/log011_subtitles_en.srt').read()[:600])
