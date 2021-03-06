import logging

import gflags

from actions.compressor import CompressorToggle
from actions.compressor import State
from actions.home import Home
#from actions.meter_dead_reckoned import MeterDeadReckoned as Meter
from actions.meter_simple import MeterSimple as Meter
from actions.led import SetLedForValve, Led
from actions.meter_bitters import MeterBitters
from actions.move import Move
from actions.move_with_ice import MoveWithIce
from actions.wait_for_glass_removal import WaitForGlassRemoval
from actions.wait_for_glass_placed import WaitForGlassPlaced
from actions.dispense_cup import DispenseCup, ReleaseCup
from actions.ice import DispenseIce, DispenseIceWithRetry, ICE_LOCATION
from actions.pressurize import HoldPressure, ReleasePressure
from actions.slam_stir import STIR_POSITION, SlamStir
from config import valve_position, ingredients
from actions.pressurize import HoldPressure, ReleasePressure

FLAGS = gflags.FLAGS

gflags.DEFINE_bool('ice', True, 'Enable ice dispensing')

def actions_for_recipe(recipe):
  """Returns the actions necessary to make the given recipe.

    recipe: manual_db.Recipe
    """
  logging.info("Enqueuing actions for recipe %s", recipe)
  actions = []
  ingredients.SubstituteIngredients(recipe.ingredients, recipe.name)
  ingredients.ReplaceWithBackups(recipe.ingredients, recipe.name)
  sorted_ingredients = sorted(
      recipe.ingredients,
      key=lambda i: -ingredients.IngredientNameToValvePosition(
        i.name, recipe.name))
  actions.append(HoldPressure())
  for ingredient in sorted_ingredients:
    valve = ingredients.IngredientNameToValvePosition(ingredient.name,
                                                      recipe.name)
    actions.append(SetLedForValve(valve, 255, 0, 0))
  if FLAGS.ice:
    actions.append(Led(max(0, -11.15 - ICE_LOCATION), 255, 255, 0, y=4))
  actions.append(Move(0))
  if FLAGS.ice:
    actions.append(MoveWithIce(ICE_LOCATION, 0.75))
    actions.append(Led(max(0, -11.15 - ICE_LOCATION), 0, 255, 0, y=4))
    actions.append(DispenseIceWithRetry(min_oz_to_meter=1.8))
    actions.append(Led(max(0, -11.15 - ICE_LOCATION), 0, 128, 255, y=4))
  ingredients_added = 0
  for ingredient in sorted_ingredients:
    ingredients_added += 1
    valve = ingredients.IngredientNameToValvePosition(ingredient.name,
                                                      recipe.name)
    actions.append(Move(valve_position(valve)))
    if ingredients_added % 1 == 0:
      actions.append(HoldPressure())
    actions.append(SetLedForValve(valve, 0, 255, 0))
    if hasattr(ingredient.qty, 'drops'):
      actions.append(MeterBitters(valve_to_actuate=valve,
                                  drops_to_meter=ingredient.qty.drops))
    elif hasattr(ingredient.qty, 'oz'):
      actions.append(Meter(valve_to_actuate=valve,
                           oz_to_meter=ingredient.qty.oz))
    else:
      raise Exception("Ingredient %s has no quantity for recipe %s:\n%s",
                      ingredient.name, recipe.name, recipe)
    actions.append(SetLedForValve(valve, 0, 128, 255))
  actions.append(Move(0.0))
  actions.append(Home(carefully=False))
  actions.append(Move(STIR_POSITION))
  actions.append(SlamStir())
  actions.append(Move(0.0))
  actions.append(Home(carefully=False))
  actions.append(WaitForGlassRemoval(recipe.user_name, recipe))
  for ingredient in sorted_ingredients:
    valve = ingredients.IngredientNameToValvePosition(ingredient.name,
                                                      recipe.name)
    actions.append(SetLedForValve(valve, 0, 0, 0))
  actions.append(WaitForGlassPlaced())
  return actions
