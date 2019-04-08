import json
import configparser
import urllib.request
import datetime
import firebase_admin
from firebase_admin import credentials, storage, firestore

# Parametros de camara
config = configparser.ConfigParser()
config.read("configDual.txt")
sector = config.get("variables", "sector")
playa = config.get("variables", "playa")
topic = playa+sector
MY_API_KEY = config.get("variables", "KEY")
titulo = config.get("variables", "titulo") + " en sector "+sector
descrip = config.get("variables", "descripcion")
imagen1 = config.get("variables", "ruta1")
imagen2 = config.get("variables", "ruta2")

# Setup
cred = credentials.Certificate('CredencialesFirebase\\miracosta-2019-credentials.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'miracosta-lpro.appspot.com'
})
db = firestore.client()

# Subida de archivos al server
bucket = storage.bucket()
fecha = str(datetime.datetime.now())
blob = bucket.blob('alertas/'+playa+'-C'+sector+'-' + fecha + 'A')
blob.upload_from_filename(imagen1)

# Crear una url con tiempo limitado
#url = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')
blob.make_public()
url = blob.public_url

blob = bucket.blob('alertas/'+playa+'-C'+sector+'-' + fecha + 'B')
blob.upload_from_filename(imagen2)

# Creacion de la deteccion en la DB
cam_ref = db.collection(u'camaras').where(u'playa', u'==', playa).where(u'sector', u'==', int(sector)).get()
for cam in cam_ref:
    print(cam.to_dict().get("playa")+str(cam.to_dict().get('sector')))
    # En vez de coger el cam.id es mejor guardar la referencia de la consulta para usar directamente
    # cam_ref.collection(u'detecciones').document().set(data)
    camid = cam.id
    data = {
        u'falsopositivo': False,
        u'noespersona': False,
        u'timestamp': fecha,
        u'url': url
    }
    print(db.collection(u'camaras').document(camid).collection(u'detecciones').document().set(data))

# Envio del json.
data = {"data": {"title": titulo, "body": descrip, "image": url}, "to": "/topics/"+topic}
message_json = json.dumps(data).encode('utf-8')
request = urllib.request.Request("https://gcm-http.googleapis.com/gcm/send", message_json,
                                 {"Authorization": "key="+MY_API_KEY, "Content-type": "application/json"})
urllib.request.urlopen(request).read()
