# Discover Monitor - Project Plan

## Google Search Console Integration

## Current Status (2025-06-23)

### Estrategia de Implementación
- [ ] Crear nuevo módulo `discover_scraper.py` basado en Playwright
- [ ] Aprovechar la clase `Article` existente para mantener consistencia
- [ ] Usar el sistema de logging configurado en el proyecto
- [ ] Implementar manejo de sesiones persistentes para Google
- [ ] Añadir soporte para múltiples cuentas de Google
- [ ] Integrar con el sistema de almacenamiento existente (CSV)

### Arquitectura Propuesta

1. **Módulo Principal (discover_scraper.py)**
   - Clase principal `DiscoverScraper` que herede de la lógica base
   - Integración con el sistema de logging existente
   - Manejo de excepciones y reintentos

2. **Gestión de Sesiones**
   - Uso de perfiles de navegador persistentes
   - Almacenamiento seguro de credenciales
   - Manejo de CAPTCHAs y verificaciones de seguridad

3. **Integración con el Proyecto**
   - Uso compartido del modelo de datos `Article`
   - Almacenamiento en el mismo formato CSV
   - Reutilización de utilidades comunes

🎉 **Major Milestone Achieved**: Reached 94% test coverage! 🎉

### Test Coverage
- **Overall Coverage**: 94% (Target: 80%) ✅ Target Achieved!
- **app.py**: 94% coverage ✅
- **scraper.py**: 95% coverage ✅
- **main.py**: 92% coverage ✅

### Plan de Implementación

1. **Preparación del Entorno**
   - [ ] Añadir dependencias a `requirements.txt`
   - [ ] Configurar variables de entorno para credenciales
   - [ ] Crear estructura básica de `discover_scraper.py`

2. **Desarrollo del Scraper**
   - [ ] Implementar autenticación con Google
   - [ ] Desarrollar navegación en el feed de Discover
   - [ ] Extraer datos de artículos usando selectores CSS/XPATH
   - [ ] Mapear datos al modelo `Article` existente

3. **Integración**
   - [ ] Conectar con el sistema de almacenamiento actual
   - [ ] Implementar detección de duplicados
   - [ ] Añadir logs detallados

4. **Monitoreo y Mantenimiento**
   - [ ] Configurar tareas programadas
   - [ ] Implementar sistema de alertas
   - [ ] Documentar el proceso de actualización

### Completed Tasks
- [x] Set up testing infrastructure (pytest, pytest-cov)
- [x] Fix failing tests in `test_app.py` and `test_app_coverage.py`
- [x] Add comprehensive tests for filter logic
- [x] Add tests for export functionality (CSV, Excel, PDF)
- [x] Add error handling tests
- [x] Create `test_app_remaining.py` for additional test coverage
- [x] Added comprehensive test coverage for `scraper.py`
- [x] Added comprehensive test coverage for `main.py`
- [x] Fixed all test failures
- [x] Implemented proper mocking for Streamlit components
- [x] Added integration tests for the full data pipeline

### Current Status
✅ All major test coverage goals have been achieved!

### Minor Improvements
- [ ] Add more edge case tests for `scraper._parse_article_from_url`
- [ ] Improve test documentation with more detailed docstrings
- [ ] Add performance benchmarks for test suite

## Próximos Pasos

### Prioridad Alta
1. **Configuración Inicial**
   - [ ] Instalar Playwright y dependencias
   - [ ] Configurar entorno de desarrollo
   - [ ] Crear estructura básica del módulo

2. **Funcionalidad Principal**
   - [ ] Implementar autenticación con Google
   - [ ] Desarrollar navegación en Discover
   - [ ] Extraer datos de artículos
   - [ ] Integrar con el almacenamiento existente

3. **Pruebas y Optimización**
   - [ ] Probar con diferentes cuentas
   - [ ] Implementar manejo de errores
   - [ ] Optimizar tiempos de ejecución
   - [ ] Monitorear uso de recursos

### Future Enhancements
- [ ] Add machine learning for content analysis
- [ ] Implement sentiment analysis on articles
- [ ] Track article performance over time
- [ ] Add alerting for new competitor content
- [ ] Integrate Google Discover scraping into the existing project structure

## Development Notes

### Required Packages
- `playwright`: For browser automation
- `python-dotenv`: For environment variables
- `pandas`: For data manipulation
- `beautifulsoup4`: For HTML parsing
- `sqlalchemy`: For database operations

### Anti-Detection Measures
- Rotate user agents
- Use residential proxies
- Randomize delays between requests
- Mimic human behavior patterns
- Handle CAPTCHAs when they appear

### Data Storage
- Store raw HTML for debugging
- Store parsed article data
- Track scraping history and success rates
- Log all errors and blocks

## Existing Project Next Steps

### High Priority
1. **Fix Remaining Test Failures**
   - [ ] Fix `test_main_success` by properly mocking Streamlit session state
   - [ ] Re-enable and fix UI tests once environment issues are resolved

2. **Improve Test Coverage**
   - [ ] Add tests for `scraper.py` (target: 80% coverage)
   - [ ] Add tests for `main.py` (target: 80% coverage)
   - [ ] Add integration tests for the full data pipeline

3. **Documentation**
   - [ ] Update README with testing instructions
   - [ ] Document test coverage requirements and practices
   - [ ] Add code comments for complex test cases

### Medium Priority
1. **CI/CD Integration**
   - [ ] Set up GitHub Actions for automated testing
   - [ ] Add coverage reporting to PRs
   - [ ] Enforce minimum coverage requirements

2. **Test Optimization**
   - [ ] Identify and remove duplicate test cases
   - [ ] Optimize slow-running tests
   - [ ] Add test data factories for better test data management

## Technical Notes

### Testing Dependencies
- pytest
- pytest-cov
- pytest-mock
- pytest-playwright (for UI tests)

### Running Tests
```bash
# Run all tests with coverage report
pytest --cov=app --cov=scraper --cov=main --cov-report=term-missing

# Run a specific test file
pytest tests/test_app.py -v

# Run tests with HTML coverage report
pytest --cov=. --cov-report=html
```

### Known Issues
- UI tests require `pytest-xvfb` which is currently disabled
- Some tests may be flaky due to timing issues with Streamlit
- PDF export tests require additional dependencies (reportlab, fpdf)

## Progress Tracking

| Date       | Coverage | Key Changes |
|------------|----------|-------------|
| 2025-06-17 | 31%      | Initial test improvements, fixed export tests |
| 2025-06-17 | 94% app.py | Added comprehensive tests for app.py |
| 2025-06-18 | 12% scraper.py | Initial test coverage for scraper.py |
| 2025-06-23 | 94% overall | Achieved target coverage for all modules |
| 2025-06-23 | 95% scraper.py | Comprehensive test coverage for scraper module |
| 2025-06-23 | 92% main.py | Comprehensive test coverage for main module |
