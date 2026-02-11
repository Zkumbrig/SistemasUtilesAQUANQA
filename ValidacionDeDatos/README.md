# 📊 Sistema de Validación de Asistencia y Horas

Aplicación web desarrollada con Streamlit para validar asistencia y horas laborales a partir de archivos Excel.

## 🚀 Características

- ✅ **Carga de archivos Excel**: Sube reportes de horas en formato .xlsx o .xls
- 📅 **Validación de asistencia por día**: Muestra las fechas laboradas por cada persona
- ⏰ **Cálculo de horas totales**: Calcula y muestra el total de horas por persona y por fecha
- 🔴 **Detección de problemas**: Resalta personas con menos de 9.58H en alguna fecha
- ⚠️ **Detección de ausencias**: Identifica personas que no asistieron todos los días
- 👥 **Información de grupo**: Muestra código de grupo, supervisor y labor de cada persona
- 📊 **Visualizaciones**: Gráficos interactivos de horas por fecha
- 💾 **Exportación**: Descarga los resultados en formato Excel

## 📦 Instalación

1. **Clona o descarga este proyecto**

2. **Instala las dependencias**:
```bash
pip install -r requirements.txt
```

## 🎯 Uso

1. **Ejecuta la aplicación**:
```bash
streamlit run app.py
```

2. **Sube tu archivo Excel** con el reporte de horas

3. **Configura las columnas**:
   - Selecciona la columna que contiene los nombres de las personas
   - Selecciona la columna de código de grupo (opcional)
   - Selecciona la columna de supervisor (opcional)
   - Selecciona la columna de labor (opcional)
   - Selecciona las columnas que representan fechas/días (puedes seleccionar múltiples)

4. **Haz clic en "Procesar Datos"**

5. **Revisa los resultados**:
   - Usa los filtros para encontrar personas con problemas
   - Selecciona una persona del menú para ver detalles
   - Revisa las horas por fecha y los gráficos
   - Exporta los resultados si lo necesitas

## 📋 Formato del Archivo Excel

El archivo Excel debe contener:
- Una columna con los nombres de las personas
- Columnas con las horas trabajadas por día/fecha
- (Opcional) Columna con código de grupo
- (Opcional) Columna con supervisor
- (Opcional) Columna con labor

### Ejemplo de estructura:

| Persona | Código Grupo | Supervisor | Labor | Lunes | Martes | Miércoles | Jueves | Viernes |
|---------|--------------|------------|-------|-------|--------|-----------|--------|---------|
| Juan Ruiz | GRP001 | Supervisor A | Operario | 9.58 | 9.58 | 0 | 9.58 | 9.58 |
| María López | GRP002 | Supervisor B | Técnico | 8.5 | 9.58 | 9.58 | 9.58 | 9.58 |

## 🔍 Validaciones Realizadas

1. **Días laborados**: Cuenta cuántos días trabajó cada persona
2. **Total de horas**: Suma todas las horas trabajadas
3. **Horas por fecha**: Muestra las horas trabajadas en cada día
4. **Validación de 9.58H**: Resalta fechas con menos de 9.58 horas
5. **Validación de asistencia completa**: Identifica personas que no trabajaron todos los días

## 📊 Funcionalidades Adicionales

- **Filtros**: Filtra personas con problemas, ausencias o horas insuficientes
- **Vista detallada**: Selecciona una persona para ver toda su información
- **Gráficos**: Visualiza las horas por fecha en gráficos de barras
- **Exportación**: Descarga los resultados validados en Excel

## 🛠️ Tecnologías Utilizadas

- **Streamlit**: Framework para aplicaciones web
- **Pandas**: Procesamiento de datos
- **OpenPyXL**: Lectura de archivos Excel
- **Plotly**: Gráficos interactivos

## 📝 Notas

- La aplicación detecta automáticamente las columnas relevantes, pero puedes configurarlas manualmente
- El mínimo de horas esperado por día es 9.58H (configurable en el código)
- Los resultados se pueden exportar para análisis adicionales

## 🤝 Contribuciones

Las mejoras y sugerencias son bienvenidas. Si encuentras algún problema o tienes ideas para nuevas funcionalidades, no dudes en compartirlas.
