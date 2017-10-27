from sqlalchemy.orm.attributes import flag_modified
from copy import deepcopy
import csv
import os.path
import re

import pycountry

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
)

criteria_code_pattern = re.compile('^\d\.\d\.\d$')


def import_example_data():
    db.drop_all()
    db.create_all()
    lang = 'en'  # assuming everything is English for now

    # Hotspots
    db.session.add_all([
        Hotspot(name={lang: 'Climate Risk'}),
        Hotspot(name={lang: 'Risk Deforestation / Biodiversity'}),
        Hotspot(name={lang: 'Pollution / Pesticides'}),
        Hotspot(name={lang: 'Risk of Landrights Violation'}),
        Hotspot(name={lang: 'Risk of Workers Right Violation'}),
        Hotspot(name={lang: 'Poverty Risk'}),
        Hotspot(name={lang: 'Transparency'}),
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
    logo_map = {
        'GSCP': {lang: 'https://ucarecdn.com/3fcc6856-4df5-4c89-862d-8f749685b922/'},
        'Fairtrade Cacao': {lang: 'https://ucarecdn.com/d789afc3-34e8-44ba-b487-55bcce8d387e/'},
        'Fairtrade': {lang: 'https://ucarecdn.com/b3f8f378-54bf-420c-ab38-a71fbf5d6b91/'},
        'RSPO': {lang: 'https://ucarecdn.com/31666604-b624-46f5-8ab3-b977df957f82/'},
        'FSC': {lang: 'https://ucarecdn.com/8c12e2c7-c021-40a8-8cb1-d1446d8bd108/'},
        'SGF': {lang: 'https://ucarecdn.com/4fd8ed9b-c0e5-40fe-b0db-de05920352a9/'},
        'GRI': {lang: 'https://ucarecdn.com/5fc14fed-4472-42be-b4d2-230b1bdd396f/'},
        'Rainforest Alliance':
        {lang: 'https://ucarecdn.com/8111e8bb-2ce9-4d57-af34-272e20acb16c/'},
        'FLA': {lang: 'https://ucarecdn.com/61b47438-2ca1-4975-aaa6-b7bd8e3f1853/'},
        'Global Coffee Platform (4C)':
        {lang: 'https://ucarecdn.com/e1511730-18e1-4343-abe8-86474733e43f/'},
        'GLOBALG.A.P': {lang: 'https://ucarecdn.com/4ca37337-ac7f-4f5f-9bc5-a898e6129f74/'},
        'BEPI': {lang: 'https://ucarecdn.com/80ea63e2-2b2e-40b3-948d-5ff4d06c9a8b/'},
        'ETI': {lang: 'https://ucarecdn.com/67549bb3-cb42-43e3-b42f-f5172abaad2f/'},
        'UTZ Cacao':
        {lang: 'https://ucarecdn.com/f64d0875-3de2-4dff-a46e-ea0bc0d4bd31/'},  # same as UTZ
        'UTZ': {lang: 'https://ucarecdn.com/f64d0875-3de2-4dff-a46e-ea0bc0d4bd31/'},
        'MSC': {lang: 'https://ucarecdn.com/4fb9ce37-9c0e-437b-a124-fb4da09da29f/'},
        'FFL': {lang: 'https://ucarecdn.com/394fdb30-bf12-4b49-b4ff-6de88eac25bf/'},
        'SAI Platform': {lang: 'https://ucarecdn.com/4e5f6129-fe89-44e3-8ee0-b2dc232cd9a8/'},
        'EU organic': {lang: 'https://ucarecdn.com/3aff3937-0062-4c89-b224-08afe40388f3/'},
        'BSCI': {lang: 'https://ucarecdn.com/23e18353-9638-4d89-aee3-e9b2bf58be50/'},
        'SA 8000': {lang: 'https://ucarecdn.com/35951758-eb0f-452f-8cdf-23886a0cb1a3/'},
        'DLG': {lang: 'https://ucarecdn.com/24d486ca-eb04-4c42-bd4d-99a2a4a7573c/'},
        'ohne GEN': {lang: 'https://ucarecdn.com/63907583-054a-4744-840c-a1a696b39e0a/'}
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
                name={lang: name},
                description={lang: description},
                countries=label_countries,
                details=dict(score=dict(
                    credibility=score_map[credibility],
                    environment=score_map[environment],
                    social=score_map[social],
                )),
                logo=logo_map[acronym]
            )
            labels[acronym] = l
            db.session.add(l)
    db.session.commit()

    # Criteria and label scores
    criteria = {}
    with open(os.path.dirname(__file__) + '/csvs/criteria-labels.csv') as csv_file:
        reader = csv.reader(csv_file)
        label_codes = next(reader)[13:32]  # ignore unknown, unscored labels for now
        for row in reader:
            # if row[11]:  # exclude from scoring
            #     continue
            (category_name, subcategory_name, criterion_name) = (row[1], row[3], row[5])
            if criterion_name == 'Consumer communication: label':
                continue  # criterion data in csv is incomplete
            criterion = Criterion.query.filter(
                Criterion.name[lang].astext == criterion_name).first()
            if criterion is None:
                subcategory = CriterionCategory.query.filter(
                    CriterionCategory.name[lang].astext == subcategory_name).first()
                if subcategory is None:
                    category = CriterionCategory.query.filter(
                        CriterionCategory.name[lang].astext == category_name).first()
                    if category is None:
                        category = CriterionCategory(name={lang: category_name})
                        db.session.add(category)
                    subcategory = CriterionCategory(
                        name={lang: subcategory_name}, category=category)
                    db.session.add(subcategory)
                criterion = Criterion(
                    name={lang: criterion_name},
                    category=subcategory,
                    details={lang: {'question': row[6], 'measures': {}}}
                )
                db.session.add(criterion)
                criteria[row[4]] = criterion
            details = deepcopy(criterion.details)
            details[lang]['measures'][int(row[9])] = row[8]
            criterion.details = details
            db.session.add(criterion)

            for label_code, s in zip(label_codes, row[13:32]):
                label = labels[label_code.strip()]
                if not s or int(s) <= 0:
                    continue
                db.session.add(LabelMeetsCriterion(
                    label=label,
                    criterion=criterion,
                    score=s,
                    explanation={lang: row[8]},
                ))
    db.session.commit()

    # Criteria translations
    with open(os.path.dirname(__file__) + '/csvs/criteria-translations.csv') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)        # Skip CSV header

        for row in reader:
            (criterion_name, criterion_question_de) = row[5], row[9]
            criterion = Criterion.query.filter(
                Criterion.name[lang].astext == criterion_name).first()

            if criterion:
                if 'de' not in criterion.details:
                    criterion.details['de'] = {}
                criterion.details['de']['question'] = criterion_question_de
                flag_modified(criterion, 'details')
            else:
                print('Criterion "{}" not found.'.format(criterion_name))

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
                if row[h.name[lang]] and not CriterionImprovesHotspot.query.get((c.id, h.id)):
                    db.session.add(CriterionImprovesHotspot(criterion=c, hotspot=h))
            db.session.add(c)
    db.session.commit()

    # Origins
    for c in pycountry.countries:
        name = c.common_name if hasattr(c, 'common_name') else c.name
        db.session.add(Origin(code=c.alpha_2, name={lang: name}))
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
        db.session.add(Origin(code=code, name={lang: name}))
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
                    resources[r] = Resource(name={lang: r})
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
                name={lang: row['Complete product Name']},
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
                    name={lang: ingredient},
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
    labels = {l.name[lang]: l for l in Label.query.all()}
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
