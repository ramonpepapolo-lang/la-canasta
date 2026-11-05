# La Canasta para iPhone y Android

La app es el asistente de lacanastaindex.com/canastas/ adentro de una app nativa (Capacitor 8): abre al instante,
funciona sin señal con los últimos precios, y cada vez que hay señal trae los precios del día de la web.
Las pestañas Precios e Índice abren la web en vivo adentro de la app.

## Qué hay acá

- `build-www.js`: arma `www/` (lo que va adentro de la app) a partir de `canastas/index.html` de la web. Correrlo siempre antes de compilar.
- `ios/`: el proyecto de Xcode (iPhone). Ícono, permisos de micrófono y reconocimiento de voz ya puestos.
- `android/`: el proyecto de Android Studio. Ícono y permiso de micrófono ya puestos.
- `capacitor.config.json`: nombre (La Canasta), identificador (com.lacanastaindex.app).

## Para publicar en el App Store (lo hace una persona con una Mac)

1. Cuenta de Apple Developer (USD 99 por año), a nombre del papá de Ramon o de la empresa: developer.apple.com/programs
2. En una Mac con Xcode: `cd app && npm install && npm run ios` (abre Xcode).
3. En Xcode: App > Signing & Capabilities > Team: elegir la cuenta. Probar en un iPhone conectado.
4. En App Store Connect (appstoreconnect.apple.com): crear la app con el identificador com.lacanastaindex.app,
   capturas de pantalla, descripción, política de privacidad (https://lacanastaindex.com/privacidad.html), categoría Compras.
5. En Xcode: Product > Archive > Distribute App > App Store Connect. Después, en App Store Connect, enviar a revisión.

## Para Google Play

1. Cuenta de Google Play Console (USD 25, una vez).
2. `cd app && npm install && npm run android` (abre Android Studio). Build > Generate Signed Bundle > Android App Bundle.
3. Subir el .aab en Play Console, con las mismas capturas y textos.

## Antes de enviar a Apple (pendiente)

- Reconocimiento de voz: el de la web funciona en Safari; adentro de la app de iPhone hay que probarlo en un iPhone real.
  Si no anda, se agrega el plugin nativo de voz (@capacitor-community/speech-recognition).
- Algo nativo de verdad, porque Apple rechaza apps que son solo una web: avisos ("la carne bajó 11% en Día hoy")
  y canastas guardadas. Están en el plan.
