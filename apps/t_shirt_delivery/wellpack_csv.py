"""Generate Wellpack CSV file"""

import copy
import csv


def generate_csv(csv_file, delivery_batch):
    """Generate wellpack CSV file

    :param text stream csv_file: CSV file
    :param class instance delivery_batch: DeliveryBatch DB model instance
    """
    t_shirts = []
    for box in delivery_batch.subsidiarybox_set.all():
        t_shirts += box.teampackage_set.all().values_list(
            "packagetransaction__t_shirt_size__name",
            "packagetransaction__t_shirt_size__code",
            "box__id",
        )
    if t_shirts:
        labels = sorted(set([i[1] for i in t_shirts]))
        labels.insert(0, "Číslo krabice")
        labels.insert(0, "ID dávky obj.")
        writer = csv.DictWriter(csv_file, fieldnames=labels)
        writer.writeheader()

        row = [[i, 0] for i in labels]
        def_row = copy.deepcopy(row)
        val_idx = 1
        prev_subsidiarybox_id = None
        rows = []
        for idx, i in enumerate(t_shirts):
            box_id = i[2]
            if prev_subsidiarybox_id and prev_subsidiarybox_id != box_id:
                rows.append(dict(row))
                row = copy.deepcopy(def_row)
            row[0][val_idx] = delivery_batch.id  # "ID dávky obj."
            row[1][val_idx] = box_id  # "Číslo krabice"
            t_shirt_code = labels.index(i[1])
            row[t_shirt_code][val_idx] += 1  # increase t-shirt size code count
            prev_subsidiarybox_id = box_id
            if idx + 1 >= len(t_shirts):
                rows.append(dict(row))
        writer.writerows(rows)
