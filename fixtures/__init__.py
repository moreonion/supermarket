from copy import deepcopy
import csv
import os.path
import re

import pycountry

from supermarket.model import (
    db,
    Brand,
    Criterion,
    CriterionImprovesHotspot,
    Hotspot,
    Ingredient,
    Label,
    LabelMeetsCriterion,
    Origin,
    Product,
    Resource,
    Retailer,
)

criteria_code_pattern = re.compile('^\d\.\d\.\d$')


def import_example_data():
    db.drop_all()
    db.create_all()

    # Hotspots
    db.session.add_all([
        Hotspot(name='Climate Risk'),
        Hotspot(name='Risk Deforestation / Biodiversity'),
        Hotspot(name='Pollution / Pesticides'),
        Hotspot(name='Risk of Landrights Violation'),
        Hotspot(name='Risk of Workers Right Violation'),
        Hotspot(name='Poverty Risk'),
        Hotspot(name='Transparency'),
    ])
    db.session.commit()

    # Labels and general scoring
    labels = {}
    score_map = {
        'red': 0,
        'no evaluation*': None,
        'red/yellow': 0,
        'red/yellow mix': 0,
        'green/yellow': 1,
        'yellow': 1,
        'green': 2,
    }
    with open(os.path.dirname(__file__) + '/csvs/Label-Info.csv') as csv_file:
        ltype = 'retailer'
        reader = csv.reader(csv_file)
        # Skip the header lines.
        for i in range(4):
            next(reader)
        for row in reader:
            if not row[1]:
                if 'Product Certification' in row[0]:
                    ltype = 'product'
                continue
            acronym, name, description = row[0], row[1], row[2]
            credibility, environment, social = row[18], row[19], row[20]
            l = Label(
                type=ltype,
                name=name,
                description=description,
                details=dict(score=dict(
                    credibility=score_map[credibility],
                    environment=score_map[environment],
                    social=score_map[social],
                )),
            )
            labels[acronym] = l
            db.session.add(l)
    db.session.commit()

    # Criteria and label scores
    criteria = {}
    for p in ['credibility', 'environment', 'social']:
        with open(os.path.dirname(__file__) + '/csvs/criteria-' + p + '.csv') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            label_codes = next(reader)[7:7+19]
            explanations = None
            for row in reader:
                # Intermediate heading
                if not row[0]:
                    continue
                if row[1]:
                    # Criterion metadata
                    c = Criterion(code=row[0], name=row[1], details=dict(
                        question=row[2],
                        explanation=row[4],
                        measures=dict(),
                    ))
                    criteria[c.code] = c
                    db.session.add(c)
                    explanations = row[7:7+19]
                else:
                    c = criteria[c.code]
                    for label_code, e, s in zip(label_codes, explanations, row[7:7+19]):
                        l = labels[label_code]
                        db.session.add(LabelMeetsCriterion(
                            label=l,
                            criterion=c,
                            score=s or None,
                            explanation=e,
                        ))
    db.session.commit()

    # Criteria and Criteria-Hotspot mapping
    with open(os.path.dirname(__file__) + '/csvs/hotspot-criteria.csv') as csv_file:
        reader = csv.DictReader(csv_file)
        hotspots = Hotspot.query.all()
        for row in reader:
            if not row['ID'] in criteria:
                print("Unknown criterion: {}".format(row['ID']))
                continue
            c = criteria[row['ID']]
            measure = row['Measures']
            details = deepcopy(c.details)
            details['measures'][int(row['Score'])] = measure
            c.details = details
            for h in hotspots:
                if row[h.name] and not CriterionImprovesHotspot.query.get((c.id, h.id)):
                    db.session.add(CriterionImprovesHotspot(criterion=c, hotspot=h))
            db.session.add(c)
    db.session.commit()

    # Origins
    for c in pycountry.countries:
        name = c.common_name if hasattr(c, 'common_name') else c.name
        db.session.add(Origin(code=c.alpha_2, name=name))
    db.session.commit()

    for code, name in [
        ('18', 'Arctic Sea'),
        ('21', 'Atlantic, Northwest'),
        ('27', 'Atlantic, Northeast'),
        ('31', 'Atlantic, Western Central'),
        ('34', 'Atlantic, Eastern Central'),
        ('37', 'Mediterranean and Black Sea'),
        ('41', 'Atlantic, Southwest'),
        ('47', 'Atlantic, Southeast'),
        ('48', 'Atlantic, Antarctic'),
        ('51', 'Indian Ocean, Western'),
        ('57', 'Indian Ocean, Eastern'),
        ('58', 'Indian Ocean, Antarctic and Southern'),
        ('61', 'Pacific, Northwest'),
        ('67', 'Pacific, Northeast'),
        ('71', 'Pacific, Western Central'),
        ('77', 'Pacific, Eastern Central'),
        ('81', 'Pacific, Southwest'),
        ('87', 'Pacific, Southeast'),
        ('88', 'Pacific, Antarctic'),
    ]:
        db.session.add(Origin(code=code, name=name))
    db.session.commit()

    # Resources
    for name in ['Cocoa', 'Palm Oil']:
        db.session.add(Resource(name=name))
    db.session.commit()

    # Products - Brands - Retailers
    products = dict()
    retailers = dict()
    brands = dict()
    with open(os.path.dirname(__file__) + '/csvs/Data_1_Example_Product.csv') as csv_file:
        for row in csv.DictReader(csv_file):
            if row['Retailer'] not in retailers:
                retailers[row['Retailer']] = Retailer(name=row['Retailer'])
            if row['Brand'] and row['Brand'] not in brands:
                brands[row['Brand']] = Brand(
                    name=row['Brand'],
                    retailer=retailers[row['Retailer']],
                )
            p = Product(
                name=row['Complete product Name'],
                gtin=row['Barcode Number (number below barcode)'],
            )
            if row['Brand']:
                p.brand = brands[row['Brand']]
            products[row['Product ID']] = p
            db.session.add(p)

    # Ingredients
    with open(os.path.dirname(__file__) + '/csvs/Data_2_Example_Ingredients.csv') as csv_file:
        next(csv_file)  # Skip header line.
        for row in csv.reader(csv_file):
            if not row[0] in products:
                print("Ingredient for unknown product: {}".format(row[0]))
                continue

            weight = 1
            for ingredient, percentage, origin in [
                    (row[i], row[i+1], row[i+2]) for i in range(4, len(row)-2, 3)]:
                if not ingredient:
                    continue
                i = Ingredient(
                    name=ingredient,
                    product=products[row[0]],
                    weight=weight,
                )
                if percentage:
                    try:
                        p = float(percentage.strip(' %').replace(',', '.'))
                        if p < 1:
                            p = int(p * 100)
                        i.percentage = p
                    except ValueError:
                        pass  # Nothing number-like in there.
                db.session.add(i)
                weight += 1

    # Product labels
    labels = {l.name: l for l in Label.query.all()}
    print(list(labels.keys()))
    with open(os.path.dirname(__file__) + '/csvs/Data_2_Example_Labels.csv') as csv_file:
        next(csv_file)  # Skip header line.
        for row in csv.reader(csv_file):
            if not row[0] in products:
                print("Label for unknown product: {}".format(row[0]))
                continue

            p = products[row[0]]
            plabels = []
            for label in row[5:]:
                if label:
                    if label.startswith('EU Biosiegel'):
                        label = 'EU organic'
                    label = label.replace('UTZ Certified', 'UTZ')
                    label = label.replace('FAIRTRADE', 'Fairtrade')
                    if label not in labels:
                        print("Unknown label '{}'".format(label))
                        continue
                    plabels.append(labels[label])
            p.labels = plabels
    db.session.commit()
