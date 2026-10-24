# Despliegue: score de pago tardío (B) y segmentación (A)

Servicio web (FastAPI en Docker) que usa, fuera del cuaderno, **el mismo modelo final del informe**:
la regresión logística sin `class_weight` de `entrega/evaluacion_B.ipynb` §3, con sus 11
predictoras. También sirve la segmentación de clientes A (K-means, k = 2, `entrega/plazo_C.ipynb`
§0) junto con lo que C propone para cada segmento.

El servicio **no contiene ni consulta los datos de la compañía**: recibe las variables ya calculadas
y devuelve la predicción. Los datos se quedan en `datos_crudos/`, que Git ignora y que la imagen
Docker no recibe.

## Qué hay aquí

| Archivo | Qué hace | ¿Necesita `datos_crudos/`? |
|---|---|---|
| `guardar_modelo.py` | Ajusta el modelo B, lo guarda en `modelos/` y verifica que reproduce las cifras publicadas de la prueba | Sí |
| `guardar_segmentacion.py` | Ajusta la segmentación A, la guarda y verifica que asigna igual que el cuaderno a los 226 clientes | Sí |
| `servicio.py` | El servicio web | No |
| `demo.html` | La página de `/demo`: formulario, barra de probabilidad, lista ordenada y tarjeta del segmento | No |
| `probar_servicio.py` | Compara el servicio con el cuaderno (local o en la nube) | Sí |
| `preparar_casos.py` | Elige los casos nuevos de la demostración y los guarda en `datos_crudos/` (`casos_demo.json` y la hoja `casos_demo.md` para el formulario) | Sí |
| `Dockerfile`, `Dockerfile.dockerignore` | Imagen del servicio; la lista de exclusión solo deja entrar el servicio, `src/cartera/` (código) y `modelos/` | No |
| `requirements.txt` | Dependencias de la imagen, con las mismas versiones con que se ajustó el modelo | — |

## Rutas del servicio

Todas, salvo `/salud`, `/demo` y `/docs` (que solo muestran páginas), exigen el token de la variable de entorno `TOKEN_API` como cabecera
`Authorization: Bearer <token>`. Si se define `TOKEN_QR`, ese segundo token también vale y se revoca por separado borrando la variable; `/demo#t=<token>` abre la página ya conectada (lo que va después de `#` no llega al servidor). En `/demo` se escribe en «Token de acceso»; en `/docs`, con el botón **Authorize**.

| Ruta | Qué devuelve |
|---|---|
| `GET /salud` | Estado y huella (sha256) de los archivos de modelo, para comprobar que es el verificado |
| `GET /modelo` | Ficha del modelo B: predictoras, categorías, versiones y la verificación contra el cuaderno |
| `POST /predecir` | Probabilidad de pago tardío (más de 30 días de atraso) de una o varias facturas. Si cada factura trae `saldo`, ordena por probabilidad × saldo, como la lista diaria |
| `POST /segmentar` | Segmento A de uno o varios clientes, con la acción que C propone y el plazo real del segmento |
| `GET /demo` | Página visual con formulario (factura y cliente). No trae datos; sus llamadas exigen el token |
| `GET /casos` | Casos preparados para llenar el formulario, si se configuraron (ver abajo). Exige el token |
| `GET /docs` | Pantalla técnica de la API |

**Cómo leer la probabilidad.** Ordena bien (AUC-PR 0,744 en la prueba frente a 0,386 de la línea
base), pero en la prueba quedó corta: sirve para priorizar, no para leerla al pie de la letra.

## Reproducirlo

Desde la raíz del repo. Los pasos 1 a 3 necesitan `datos_crudos/` y el entorno del proyecto
(`requirements.txt`, Python 3.14.5).

```bash
# 1. Ajustar, guardar y verificar los modelos (crea modelos/*.joblib y sus fichas *.json)
.venv/bin/python app/guardar_modelo.py
.venv/bin/python app/guardar_segmentacion.py

# 2. Construir la imagen (desde la raíz; la lista de exclusión deja fuera datos_crudos/)
docker build --platform linux/amd64 -f app/Dockerfile -t score-b .

# 3. Levantarla en local con un token propio
docker run --rm -p 8000:8000 -e TOKEN_API=<token> score-b
# Abrir http://localhost:8000/demo

# 4. Verificar el servicio contra el cuaderno (necesita además fastapi y httpx en el entorno)
TOKEN_API=<token> .venv/bin/python app/probar_servicio.py --url http://localhost:8000
```

**Casos preparados (opcional).** Para que `/demo` muestre la lista «Caso preparado», el servicio lee `datos_crudos/casos_demo.json` (generado por `preparar_casos.py`). Nunca entra a la imagen: en local se monta de solo lectura con `-e CASOS_DEMO_ARCHIVO=/srv/casos/casos_demo.json -v "$PWD/datos_crudos/casos_demo.json:/srv/casos/casos_demo.json:ro"`, y en Azure va como secreto (`CASOS_DEMO=secretref:casos-demo`). Sin ellos, el formulario se llena a mano.

Sin Docker: `pip install -r app/requirements.txt` y
`TOKEN_API=<token> uvicorn app.servicio:app --port 8000` desde la raíz.

## En la nube (Azure Container Apps)

Con Azure CLI y una sesión iniciada (`az login`). Los nombres son los usados por el equipo; el del
registro debe ser único en Azure. La región tiene que ser una de las que permita la suscripción
(Azure for Students restringe las regiones).

```bash
az group create -n rg-pfi-score-b -l brazilsouth
az acr create -g rg-pfi-score-b -n <registro> --sku Basic --admin-enabled true
az acr login -n <registro>
docker tag score-b <registro>.azurecr.io/score-b:1.5
docker push <registro>.azurecr.io/score-b:1.5
az containerapp env create -g rg-pfi-score-b -n env-pfi-score-b -l brazilsouth --logs-destination none
az containerapp create -g rg-pfi-score-b -n score-b --environment env-pfi-score-b \
  --image <registro>.azurecr.io/score-b:1.5 --registry-server <registro>.azurecr.io \
  --registry-username <registro> --registry-password <contraseña del registro> \
  --secrets token-api=<token> --env-vars TOKEN_API=secretref:token-api \
  --ingress external --target-port 8000 --cpu 0.5 --memory 1.0Gi --min-replicas 1 --max-replicas 1
```

El token queda como secreto de Container Apps, no en el código ni en la imagen. La réplica mínima
en 1 evita el arranque en frío durante la demostración; después de la sustentación el servicio se
suspende:

```bash
az containerapp update -g rg-pfi-score-b -n score-b --min-replicas 0
az group delete -n rg-pfi-score-b   # elimina todo lo creado
```

## Qué se verificó

- El modelo B leído desde `modelos/` reproduce las cifras que `evaluacion_B.ipynb` §3 publicó para
  la prueba: 3.970 facturas, AUC-PR 0,744, AUC-ROC 0,829, Brier 0,177 y los 10 tramos de la tabla
  de calibración.
- En 200 facturas de la prueba, el servicio (en el proceso, en el contenedor local y en Azure) da
  la misma probabilidad que el Pipeline del cuaderno, a 4 decimales.
- La segmentación A asigna el mismo segmento que `plazo_C.ipynb` a los 226 clientes (171 y 55), y
  el servicio lo mismo a los 68 clientes de prueba.
- Los archivos de modelo solo contienen parámetros resumidos (medianas, medias, escalas, límites de
  recorte, categorías anonimizadas, coeficientes y centros). Se comprobó que no llevan ningún NIT ni
  `id_saldo`, y la imagen no contiene ningún archivo de datos de la compañía.
- Sin token o con un token incorrecto el servicio responde 401.
