data = \
{
  "status": "ok",
  "version": "v1",
  "schedule_id": "2014-03-18",
  "table_name": "Outer table",
  "data": [
    {
      "data": [
        {
          "year": "2009",
          "values": [
            {
              "version": "v1",
              "data": [
                {
                  "data": [
                    {
                      "year": "2009",
                      "values": [42],
                    }
                  ],
                  "schedule_id": "2014-03-18",
                  "table_name": "Inner Table",
                  "unit": "Percent"
                }
              ]
            }
          ],
        }
      ],
    }
  ]
}

print(data)

res = data.get('data', [{}])[0].get('data')[0].get('values', [{}])[0].get('data')[0].get('schedule_id')
print(res)


## The transformation

from glom import glom

target = {'data': {'id': 2, 'date': '1999-01-01'}}

response = {'id': glom(target, 'data.id'),
            'date': glom(target, 'data.date')}

response = glom(target, {'id': 'data.id',
                          'date': 'data.date'})
