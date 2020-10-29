"""Main farm access."""

from __future__ import annotations
from farmer.ext.log import Expense, Harvest, Log, Observation, Seeding, Transplanting
from farmer.ext.term import CropFamily, Season, Unit, Crop
from farmer.ext.others import Content, Quantity

import os
from datetime import datetime
from typing import Dict, Generator, Iterable, List, Type

from farmOS import farmOS
from farmer.ext.area import Area
from farmer.ext.asset import Asset, Equipment, Planting


def farm():
    """Access to farm with provided credentials."""
    return Farm()


class Farm(farmOS):

    def __init__(self):
        self._host = None
        self._user = None
        self._pass = None

        if os.path.exists("farmos.cfg"):
            with open('farmos.cfg') as cfg:
                for line in cfg.readlines():
                    if line.startswith("HOST"):
                        self._host = line[line.index("=")+1:].strip()
                    if line.startswith("USER"):
                        self._user = line[line.index("=")+1:].strip()
                    if line.startswith("PASS"):
                        self._pass = line[line.index("=")+1:].strip()
            if not self._host:
                Exception("HOST key is not defined in farmos.cfg")
            if not self._user:
                Exception("USER key is not defined in farmos.cfg")
            if not self._pass:
                Exception("PASS key is not defined in farmos.cfg")
        super().__init__(self._host)
        self._token = self.authorize(self._user, self._pass)

    @property
    def content(self) -> Content:
        return Content(self, keys=self.info())

    @property
    def seasons(self) -> Iterable[Season]:
        for season in self.term.get("farm_season")['list']:
            yield Season(self, season)

    @property
    def assets(self) ->  Iterable[Asset]:
        for asset in self.asset.get()['list']:
            yield Asset(self, keys=asset)

    @property
    def areas(self) -> Iterable[Area]:
        for area in self.area.get()['list']:
            Area(self, keys=area)

    @property
    def crop_families(self) -> Iterable[CropFamily]:
        for fam in self.term.get("farm_crop_families")['list']:
            yield CropFamily(self, keys=fam)

    @property
    def crops(self) -> Iterable[Crop]:
        for crop in self.term.get("farm_crops")['list']:
            yield Crop(self, crop)

    @property
    def equipment(self) ->  Iterable[Equipment]:
        for equip in self.asset.get({ 'type': 'equipment' })['list']:
            yield Equipment(self, equip)

    @property
    def plantings(self) -> Iterable[Planting]:
        for planting in self.asset.get({ 'type': 'planting' })['list']:
            yield Planting(self, planting)

    @property
    def expenses(self) ->  Iterable[Expense]:
        for log in self.log.get({ 'type': 'farm_activity' })['list']:
            yield Expense(self, log)

    @property
    def units(self) -> Iterable[Unit]:
        for unit in self.term.get('farm_quantity_units')['list']:
            yield Unit(self, unit)

    @property
    def harvests(self) -> Iterable[Harvest]:
        return self._get_logs('farm_harvest', Harvest)

    @property
    def seedings(self) -> Iterable[Seeding]:
        return self._get_logs('farm_seeding', Seeding)

    @property
    def transplants(self) -> Iterable[Transplanting]:
        return self._get_logs('farm_transplanting', Transplanting)

    @property
    def observations(self) -> Iterable[Observation]:
        return self._get_logs('farm_observation', Observation)


    def _get_logs(self, typ: str, obj_class:  Type[Log]) -> Iterable[Type[Log]]:
        for log in self.log.get({'type': typ})['list']:
            yield obj_class(self, log)

    def _create_log(self, name: str, date: datetime, category: str, fields: Dict, done=False):
        data = {
            "name": name,
            "timestamp": str(int(datetime.timestamp(date))),
            "log_category": [{
                "name": category
            }],
            "type": "farm_observation"
        }
        data.update(fields)
        if 'done' not in data:
            data['done'] = '1' if done else '0'
        ret = self.log.send(data)
        return ret

    def create_planting(self, crop: Crop, season: str, location: str) -> Planting:
        ret = self.asset.send({
            "name": "{} {} {}".format(season, location, crop.name),
            "type": "planting",
            "crop": [
                {
                    "id": crop.tid
                }
            ],
            "season": [{"name": season}]
        })
        plant = Planting(self, keys=ret)
        self._planting.append(plant)
        return plant

    def create_seeding(self, planting: Planting, location: Area, crop: Crop, date: datetime, seeds: int, source=None, done=False) -> Seeding:
        name = "Seed {} {} {}".format(date.year, location.name, crop.name)
        fields = {
            "type": "farm_seeding",
            "asset": [
                {
                    "id": planting.id,
                    "resource": "taxonomy_term"
                }
            ],
            "seed_source": source,
            "movement": {
                "area": [
                    {
                        "id": location.tid,
                        "resource": "taxonomy_term"
                    }
                ]
            },
            "quantity": [
                {
                    "measure": "count",
                    "value": str(seeds),
                    "unit": {
                        'name': 'Seeds',
                        "resource": "taxonomy_term"
                    }
                }
            ]
        }
        ret = self._create_log(name, date, 'Plantings', fields, done=done)
        return Seeding(self, keys=ret)

    def create_transplant(self, planting: Planting, location: Area, date: datetime, fields=None, done=False):
        name = "Transplant {}".format(planting.name)
        data = {
            "type": "farm_transplanting",
            "movement": {
                "area": [
                    {
                        "id": location.tid,
                        "resource": "taxonomy_term"
                    }
                ]
            },
            "asset": [
                {
                    "id": planting.id,
                    "resource": "taxonomy_term"
                }
            ]
        }
        if fields:
            data.update(fields)
        ret = self._create_log(name, date, 'Plantings', data, done=done)
        return Transplanting(self, ret)

    def create_harvest(self, planting: Planting, date: datetime, quantities: List[Quantity], done=False):
        name = "Harvest {} {}".format(date.year, planting._crop[0]['name'])
        data = {
            "type": "farm_harvest",
            "asset": [{
                "id": planting.id,
                "resource": "taxonomy_term"
            }]
        }

        if quantities:
            data["quantity"] = []
            for quantity in quantities:
                data["quantity"].append(quantity.to_dict())

        ret = self._create_log(name, date, 'Plantings', data, done=done)
        return Harvest(self, ret)

    def create_log(self, name: str, date: datetime, category: str, fields: Dict, done=False):
        return Log(self, self._create_log(name, date, category, fields, done))
