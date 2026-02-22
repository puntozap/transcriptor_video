# Seccion: Creador de Imagenes

## Objetivo
Crear una nueva seccion en la app llamada **Creador de Imagenes** con dos subpestañas:
- **Imagen vertical** (1080x1920)
- **Imagen horizontal** (1280x720)

La seccion permitira componer imagenes para Instagram/miniaturas con preview en la misma UI.

## Capas (orden estricto)
1. **Fondo** (siempre abajo, modo fill al formato).
2. **Imagen principal PNG** (sin fondo, responsive con fill estetico).
3. **Texto superior** (opcional, estilo badge como ejemplo, colores editables).
4. **Titulo** (centrado debajo de la imagen principal).
5. **Nombre** (debajo del titulo).
6. **Logo** (movible).

## Requisitos de contenido
- **Fondo**: siempre fill al formato (sin barras).
- **Imagen principal PNG**: posicion ajustable (x, y), fill responsive sin perder estetica.
- **Texto superior**: estilo badge con fondo redondeado y colores editables.
- **Fuentes**: Arial / Arial Bold, con tamaño editable por sliders.
- **Logo**: movible (x, y).

## Exportacion
- Exportar en **PNG** y **JPG**.

## Preview en UI
- Vista previa dentro de la misma UI.
- Boton para renderizar preview y boton para exportar en alta resolucion.

## UI (primer borrador)
**Layout general (3 columnas):**
- **Izquierda (Opciones)**: todos los controles con scroll vertical.
- **Centro (Visual)**: preview en vivo.
- **Derecha (Extra/Vista)**: exportaciones, presets y resumen de parametros.

**Opciones (con scroll):**
- Selector de fondo (imagen).
- Selector de imagen principal (PNG).
- Toggle texto superior + texto + colores + tama?o.
- Texto de titulo + tama?o.
- Texto de nombre + tama?o.
- Selector de logo + posicion (x, y) + escala.
- Controles de posicion y escala para imagen principal.
- Boton **Generar preview**.
- Boton **Exportar PNG/JPG**.

**Controles con carousels e inputs:**
- Carousels para seleccionar presets de estilo (colores, badge, tipografia).
- Inputs numericos para tamanos, posiciones y escalas.
- Sliders para ajustes finos (x, y, escala, opacidad).

## Mecanismo de programacion (plan tecnico)
1. **Nueva pesta?a** en `ui/tabs/` llamada `imagen_creator_tab.py` con dos subpesta?as:
   - `Imagen vertical` (1080x1920)
   - `Imagen horizontal` (1280x720)
2. **Layout 3 columnas** usando `CTkFrame` con `grid`:
   - Columna izquierda con `CTkScrollableFrame` para todas las opciones.
   - Columna central con `CTkLabel` para renderizar preview (usar `PIL.ImageTk`).
   - Columna derecha con acciones: exportar, presets, reset, y resumen.
3. **Estado compartido** en `ui/shared/state.py` para guardar todas las opciones.
4. **Compositor** en `core/image_composer.py`:
   - Usa Pillow para componer capas.
   - Modo `fill` para fondo y PNG principal (scale + crop centrado).
   - Render en dos modos:
     - **preview** (resolucion baja, rapido)
     - **final** (resolucion exacta, export PNG/JPG)
5. **Actualizacion del preview**:
   - Boton "Generar preview" y opcion de auto-refresh al mover sliders.
6. **Exportacion**:
   - Guardar en `output/{base}/imagenes/` como PNG y JPG.
   - Mantener nombres con timestamp.
