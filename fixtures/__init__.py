from copy import deepcopy
import csv
import os.path
import re

import pycountry
import sqlalchemy as sa

from supermarket.model import (
    db,
    Brand,
    Criterion,
    CriterionCategory,
    CriterionImprovesHotspot,
    Hotspot,
    Ingredient,
    Label,
    LabelCountry,
    LabelMeetsCriterion,
    Origin,
    Product,
    Resource,
    Retailer,
    Translation,
    TranslatedString,
    TranslatedText
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
    label_countries = [LabelCountry(code='*')]  # all labels are international for now
    score_map = {
        'red': 1,
        'no evaluation*': 1,
        'red/yellow': 1,
        'red/yellow mix': 1,
        'green/yellow': 2,
        'yellow': 2,
        'green': 3,
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
            t = Translation()

            l = Label(
                translation=t,
                type=ltype,
                countries=label_countries,
                details=dict(score=dict(
                    credibility=score_map[credibility],
                    environment=score_map[environment],
                    social=score_map[social],
                )),
            )
            name = TranslatedString(
                value=name, language='en', field='name',
                translation=t
            )
            description = TranslatedText(
                value=description, language='en', field='description',
                translation=t
            )
            l.name = [name]
            l.description = [description]
            labels[acronym] = l
            db.session.add(l)
    db.session.commit()

    # Criteria and label scores
    criteria = {}
    with open(os.path.dirname(__file__) + '/csvs/criteria-labels.csv') as csv_file:
        reader = csv.reader(csv_file)
        label_codes = next(reader)[13:]
        for row in reader:
            if row[11]:  # exclude from scoring
                continue
            (category_name, subcategory_name, criterion_name) = (row[1], row[3], row[5])
            criterion = None
            result = db.session.query(Criterion, Translation, TranslatedString).filter(
                sa.and_(TranslatedString.translation_id == Criterion.translation_id,
                        TranslatedString.value == criterion_name)).first()
            if result is not None:
                criterion = result[0]

            if criterion is None:
                subcategory = CriterionCategory.query.filter_by(name=subcategory_name).first()
                if subcategory is None:
                    category = CriterionCategory.query.filter_by(name=category_name).first()
                    if category is None:
                        category = CriterionCategory(name=category_name)
                        db.session.add(category)
                    subcategory = CriterionCategory(name=subcategory_name, category=category)
                    db.session.add(subcategory)
                t = Translation()
                criterion = Criterion(
                    translation=t,
                    category=subcategory,
                    details={'question': {'value': row[6], 'language': 'en'}, 'measures': {}}
                )
                name = TranslatedString(
                    value=criterion_name, language='en', field='name',
                    translation=t
                )
                criterion.name = [name]
                db.session.add(criterion)
                criteria[row[4]] = criterion
            details = deepcopy(criterion.details)
            details['measures'][int(row[9])] = {'value': row[8], 'language': 'en'}
            criterion.details = details
            db.session.add(criterion)

            for label_code, s in zip(label_codes, row[13:]):
                label = labels[label_code.strip()]
                if not s or int(s) <= 0:
                    continue
                t = Translation()
                exp = TranslatedText(value=row[8], language='en',
                                     field='explanation', translation=t)
                db.session.add(LabelMeetsCriterion(
                    label=label,
                    criterion=criterion,
                    score=s,
                    explanation=[exp],
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

    # Resources and Resource label mapping
    resources = {}
    with open(os.path.dirname(__file__) + '/csvs/labels-resources.csv') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        next(reader)
        for row in reader:
            l, rs = row[0].strip(), row[1]
            if rs == 'n.a.' or rs.startswith('all '):
                continue
            label = labels[l]
            for r in (r.strip() for r in rs.split(',')):
                if r not in resources:
                    resources[r] = Resource(name=r)
                label.resources.append(resources[r])

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

    # @TODO: Needs better solution for multiple languages
    labels = {l.name[0].value: l for l in Label.query.all()}
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
                        label = 'EU Organic'
                    label = label.replace('UTZ Certified', 'UTZ')
                    label = label.replace('UTZ Kakao', 'UTZ Cacao')
                    label = label.replace('FAIRTRADE', 'Fairtrade')
                    label = label.replace('RSPO', 'Roundtable on Sustainable Palm Oil (RSPO)')
                    if label not in labels:
                        print("Unknown label '{}'".format(label))
                        continue
                    plabels.append(labels[label])
            p.labels = plabels
    db.session.commit()
