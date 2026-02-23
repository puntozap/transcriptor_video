# TikTok - Configuracion y Conexion (Plan)

Este documento describe los pasos necesarios para habilitar la conexion y publicacion en TikTok desde la app.

## 1. Crear cuenta de desarrollador (pasos exactos)
1. Abre el portal de registro y crea tu cuenta con email.
2. Ingresa tu email, acepta los terminos y solicita el PIN.
3. Verifica el PIN en tu email y completa el registro.

Link oficial (registro):
```
https://developers.tiktok.com/signup/
```

## 2. Crear organizacion y app (pasos exactos)
1. En TikTok for Developers, abre **Developer Portal**.
2. En **My organizations**, crea una organizacion (nombre de tu empresa).
3. En **Manage apps**, presiona **Connect an app**.
4. Selecciona la organizacion como owner y completa el registro del app.

Referencias oficiales:
```
https://developers.tiktok.com/doc/getting-started-create-an-app
```
```
https://developers.tiktok.com/doc/set-up-developer-portal-account
```

Ejemplos:
- Local: `http://127.0.0.1:8766/callback`
- Con proxy: `https://tudominio.com/callback`

## 3. Configurar Login Kit + Redirect URI
1. En tu app, habilita **Login Kit**.
2. Registra los Redirect URI (pueden ser http/https, hasta 10).
3. Usa el Redirect URI en tu flujo OAuth de escritorio.

Referencia oficial (Desktop Login Kit):
```
https://developers.tiktok.com/doc/login-kit-desktop/
```

## 4. Scopes requeridos
Para publicar videos se debe solicitar el scope:
- `video.publish`

Otros scopes opcionales:
- `user.info.basic`

Nota: TikTok requiere aprobacion para `video.publish`.

## 5. Modos de publicacion
TikTok soporta dos modos principales:
1. **FILE_UPLOAD**: sube el archivo local directamente.
2. **PULL_FROM_URL**: TikTok descarga desde una URL publica.

Recomendacion: **FILE_UPLOAD** para evitar validacion de dominios.

## 6. Requisitos de video
- Formato MP4 recomendado.
- Codec H.264 + AAC.
- Tamaño y duracion dentro de los limites de TikTok.

## 7. Tokens y OAuth
1. Implementar flujo OAuth con Login Kit.
2. Guardar `access_token` y `refresh_token`.
3. Renovar token cuando expire.

## 8. Proceso de publicacion (alto nivel)
1. Usuario se conecta con TikTok (OAuth).
2. Se obtiene token + user info.
3. Se sube el video (FILE_UPLOAD o PULL_FROM_URL).
4. Se publica el video en la cuenta.

## 9. Integracion en la app (a implementar)
- Nueva pestaña TikTok en UI.
- Boton "Conectar TikTok" (OAuth).
- Guardado de credenciales en `credentials/tiktok_config.json`.
- Seccion de subida (archivo local o URL).
