# Sistema de Programacion y Publicacion en Redes Sociales

## Objetivo
Construir un sistema web para cargar productos, programar publicaciones por plataforma y ejecutar la publicacion automaticamente en una fecha/hora especifica. Una vez publicada cada pieza, el sistema debe eliminar los archivos (no se conserva almacenamiento de media).

El sistema web se apoya en un programa base de escritorio que usa una API: cada video creado en el programa se sube directamente a la web.

revisar como funciona todo en C:\laragon\www\transcriptor_video de acuerdo a las pesta;as

## Alcance
Plataformas y formatos soportados:
- YouTube (long form)
- Shorts
- Instagram Post
- Instagram Reels
- Instagram Stories

El sistema debe permitir multiples destinos por producto y manejar programacion por destino.

Integracion clave:
- El programa base genera videos y los sube via API al sistema web.
- El sistema web recibe, almacena temporalmente, programa y publica.

## Flujo funcional (paso a paso)
1. Cargar producto y archivos (video/imagen/miniatura) desde la web o via API (programa base).
2. Crear destino(s) para el producto (YouTube, Shorts, Instagram Post, Reels, Stories).
3. Configurar metadatos por destino (titulo, descripcion, hashtags, tags, miniatura, privacidad, etc.).
4. Definir fecha y hora de publicacion por destino (zona horaria obligatoria).
5. Validar requisitos por plataforma (duracion, formato, relacion de aspecto, tamanos).
6. Guardar en cola de publicacion.
7. Ejecutar publicacion automatica al llegar la fecha/hora.
8. Registrar resultado (exito o error).
9. Eliminar archivos locales (borrar assets) una vez publicado.
10. Mantener solo metadatos y logs minimos.

## Reglas clave
- Los archivos de media se eliminan despues de publicar (no se almacena contenido).
- No se permite publicar sin fecha/hora programada.
- Cada destino puede fallar sin bloquear a los demas.
- El sistema debe ser idempotente: reintentos no deben duplicar publicaciones.

## Modelo de datos (base)

### Product
- id
- name
- status (draft | scheduled | published | failed)
- created_at
- updated_at

### Asset
- id
- product_id
- type (video | image | thumbnail)
- filename
- storage_path (temporal)
- mime_type
- size_bytes
- duration_seconds
- width
- height
- deleted_at

### Destination
- id
- product_id
- platform (youtube | shorts | instagram)
- format (long | short | post | reel | story)
- scheduled_at
- timezone
- status (draft | scheduled | publishing | published | failed)
- published_at
- error_message

### DestinationMetadata
- id
- destination_id
- title
- description
- hashtags
- tags
- thumbnail_asset_id (nullable)
- privacy (public | unlisted | private)
- other_json (flexible)

### PublishLog
- id
- destination_id
- event (queued | started | success | fail | deleted_assets)
- message
- created_at

## Estados y transiciones
- draft -> scheduled -> publishing -> published
- draft -> scheduled -> publishing -> failed
- failed -> scheduled (retry manual)

## Validaciones por plataforma (basico)
- YouTube: video horizontal, duracion mayor a 60s (long form)
- Shorts: video vertical, duracion <= 60s
- Instagram Post: imagen o video con formatos soportados
- Instagram Reels: video vertical, duracion segun regla de la plataforma
- Instagram Stories: video vertical o imagen, duracion corta

## Reglas editoriales internas (solo Instagram)
Estas reglas son recomendaciones internas para evitar engagement bait en captions.

### Prompt anti-engagement-bait (para generar descripciones)
```
Redacta una descripcion para Instagram con tono natural y util. 
Evita pedir acciones de engagement de forma directa (ej: "comenta", "comenta si", 
"etiqueta a", "manda DM", "comparte", "dale like", "guarda", "sigue"). 
Evita premios o condicionamientos ("si comentas te envio", "si compartes te doy", 
"comenta para recibir"). 
Permite una unica invitacion suave y opcional a la conversacion (ej: "si te resuena, 
cuentame tu experiencia"). 
Maximo 2 lineas, sin emojis, sin mayusculas en exceso.
```

### Trial Reels (comportamiento esperado)
- Un Trial Reel se muestra primero a no seguidores.
- Luego se puede convertir a visibilidad total:
  - Manual: "Share with everyone" cuando decidas.
  - Auto: Instagram puede compartirlo automaticamente si performa bien.
- El sistema debe exponer estas dos opciones al crear un Reel con modo Trial.

## Eliminacion de archivos
- Despues de publicacion exitosa: eliminar assets locales.
- Registrar evento `deleted_assets` en PublishLog.
- Guardar solo metadata y logs.

---

# Modulo: Creador de Imagenes

## Objetivo
Construir un editor interno para generar imagenes listas para publicar (posts, thumbnails, stories, reels). Debe permitir crear composiciones con capas, textos, presets y exportar en tamaños correctos por plataforma.

## Alcance del creador
- Generar imagenes para:
  - Instagram Post (1080x1080)
  - Instagram Story (1080x1920)
  - Reels cover (1080x1920)
  - YouTube thumbnail (1280x720)
- Permitir dos modos basicos:
  - Modo plantilla (presets predefinidos)
  - Modo manual (control total de capas y textos)

## Componentes funcionales
1. **Preset Manager**
   - Lista de presets con colores, tipografia y layout.
   - Boton para aplicar preset sobre el canvas.
   - Posibilidad de guardar un preset nuevo.

2. **Canvas / Preview**
   - Preview en tiempo real.
   - Zoom y desplazamiento.
   - Opcion de renderizado rapido (baja calidad) y final (alta calidad).

3. **Capas (Layers)**
   - Background (color o imagen)
   - Imagen principal (PNG con transparencia)
   - Texto superior, titulo, subtitulo, nombre
   - Logo / marca
   - Cada capa debe ser movable, escalable y rotatable

4. **Tipografia**
   - Selector de fuentes (bold y regular)
   - Buscador por nombre
   - Preview de fuente al pasar el cursor
   - Definir tamaños por capa

5. **Colores y estilo**
   - Picker de colores para cada texto
   - Colores de fondo y overlays
   - Bordes, sombras y opacidad basica

6. **Exportacion**
   - Exportar a PNG y JPG
   - Nombre automatico + nombre personalizado
   - Guardar en carpeta temporal

## Requerimientos tecnicos
- El creador debe cargar fuentes disponibles en el sistema.
- Si hay muchas fuentes, la carga debe ser lazy (solo cuando se abre el panel de fuentes).
- La preview no debe bloquear la UI; usar threading.
- El render final debe ser estable con PIL/Pillow.

## Flujo del creador
1. Seleccionar tamaño de salida (ej: 1080x1080, 1080x1920, 1280x720)
2. Elegir preset inicial (opcional)
3. Cargar imagen principal
4. Ajustar textos, colores, posicion y escala
5. Previsualizar
6. Exportar

## Modelo de datos (configuracion del creador)
### ImageCreatorState
- id
- preset_id
- output_size
- background_color
- background_image_path
- main_image_path
- text_top
- text_title
- text_subtitle
- text_name
- font_bold
- font_regular
- color_top
- color_title
- color_subtitle
- color_name
- logo_path
- export_format (png | jpg)

## Acciones para el agente
- Construir el modulo de creacion de imagenes con preset + manual.
- Implementar selector de tamaño con plantillas.
- Implementar sistema de capas con controles (posicion, escala, rotacion).
- Implementar selector de fuentes con busqueda + preview.
- Implementar exportacion y guardado temporal.
- Integrar salida con el sistema de productos (asset generado se asocia a Product).

## Entregables esperados
- UI funcional del creador con presets.
- Exportacion correcta de imagenes en tamanos definidos.
- Guardado temporal de assets y limpieza posterior.
- Documentacion breve de uso.
