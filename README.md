# GDT Max Calculator

Esta utilidad replica el algoritmo de puntuación de reseñas utilizado en el
videojuego **Game Dev Tycoon** creado por Greenheart Games. El objetivo es
explorar combinaciones de puntos de Diseño y Tecnología para encontrar el
proyecto con el puntaje interno más alto posible y estimar la calificación de
las reseñas que recibiría el juego.

## Requisitos

- Python 3.9 o superior.

## Uso rápido

1. Crea un entorno virtual (opcional pero recomendado).
2. Ejecuta el script directamente desde la terminal:

   ```bash
   python gdt_score_calculator.py
   ```

   Esto imprimirá el mejor puntaje interno (`g`), la puntuación final prevista
   y los parámetros necesarios para conseguirla, explorando un rango de valores
   predefinido.

## Usar el módulo desde tu propio código

El archivo `gdt_score_calculator.py` define dos piezas principales:

- `ReviewAlgorithm`: clase que implementa el cálculo del puntaje interno y la
  calificación final.
- `simulate_best_game`: función auxiliar que examina un rango de valores de
  Diseño/Tecnología (y combinaciones de investigación) para hallar el mejor
  resultado.

Ejemplo de uso:

```python
from gdt_score_calculator import GameParameters, ReviewAlgorithm

params = GameParameters(
    design_points=120,
    tech_points=140,
    genre="Strategy",
    size="Medium",
    platform_factor=1.1,
    audience_factor=1.05,
    bug_ratio=0.0,
    multi_platform_penalty=0.9,
    trend_factor=1.2,
    extra_quality=0.05,
    target_game_score=350.0,
    expertise_limit=10.0,
)

algo = ReviewAlgorithm()
g_score = algo.calculate_game_score(params)
rating = algo.calculate_final_rating(g_score, params.target_game_score, params.expertise_limit)

print(g_score, rating)
```

Modifica los parámetros para simular diferentes tamaños de proyectos,
plataformas, audiencias o penalizaciones por bugs según los datos que manejes
del juego.

## Licencia

El proyecto se distribuye bajo la licencia MIT incluida en `LICENSE`.

