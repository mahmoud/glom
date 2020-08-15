data = \
{
  "status": "ok",
  "version": "v1",
  "sched_date": "2016-05-12",
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
                  "sched_date": "2014-03-18",
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

data.get('data', [{}])[0]

res = data.get('data', [{}])[0].get('data')[0].get('values', [{}])[0].get('data')[0].get('sched_date')
print(res)


## The transformation

from glom import glom

target = {'ID': 2, 'data': {'isoDate': '1999-01-01'}}

response = {'id': glom(target, 'ID'),
            'date': glom(target, 'data.isoDate')}

response = glom(target, {'id': 'ID',
                         'date': 'data.isoDate'})
print(response)


EMAIL_SPEC = {'id': 'email_id',
              'email': 'email_addr',
              'type': 'email_type'}

def get_all_emails(filters):
    queryset = Email.objects.filter(**filters)

    all_emails_spec = {'results': [EMAIL_SPEC]}

    return glom(queryset, all_emails_spec)
