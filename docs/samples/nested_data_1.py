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
