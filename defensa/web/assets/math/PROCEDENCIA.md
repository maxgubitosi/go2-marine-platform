# Procedencia de las ecuaciones del deck

Generado por `defensa/scripts/render_math.py`. No editar a mano.

Los números de ecuación salen de `informe/main.aux`, o sea de la última
compilación del informe. Si el informe se recompila y la numeración se
corre, hay que volver a correr el script y actualizar las citas de las
láminas.

| SVG | Ecuación en el informe | Línea en `main.tex` | `\label` |
|---|---|---|---|
| `body_to_feet.svg` | (20) | 1927 | `eq:body_variation_to_feet` |
| `commands.svg` | sin numerar | 2282 | `-` |
| `contact_constraint.svg` | (15) | 1748 | `eq:contact_velocity_constraint` |
| `dof_count.svg` | sin numerar | 1748 | `-` |
| `ema.svg` | sin numerar | 2365 | `-` |
| `intrinsics.svg` | (3) | 1102 | `eq:camera_intrinsics` |
| `lab_response.svg` | sin numerar | 3385 | `-` |
| `leg_ik.svg` | (23) | 1984 | `eq:leg_inverse_differential_kinematics` |
| `marine_dynamics.svg` | (8) | 1314 | `eq:marine_dynamics` |
| `marine_kinematics.svg` | (7) | 1293 | `eq:marine_kinematics` |
| `pinhole.svg` | (2) | 1079 | `eq:pinhole_projection` |
| `pnp.svg` | (6) | 1160 | `eq:pnp_optimization` |
| `quadruped_dynamics.svg` | (14) | 1717 | `eq:quadruped_dynamics` |
| `reduced_state.svg` | (9) | 1340 | `eq:reduced_marine_state` |
| `transform_chain.svg` | (26) | 2132 | `eq:camera_marker_chain` |
| `wave_field.svg` | (11) | 1430 | `eq:sinusoidal_wave_model` |
| `wave_harmonic.svg` | (12) | 1453 | `eq:harmonic_wave_model` |
