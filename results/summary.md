# Results

## Accuracy

Difficulty columns show the automatic score.

| run                      | automatic   | after human review   | easy        | medium      | hard       | unanswerable   |
|:-------------------------|:------------|:---------------------|:------------|:------------|:-----------|:---------------|
| openai/gpt-oss-120b / v1 | 30% (12/40) | 30% (12/40)          | 58% (7/12)  | 25% (4/16)  | 10% (1/10) | 0% (0/2)       |
| openai/gpt-oss-120b / v2 | 90% (36/40) | 98% (39/40)          | 92% (11/12) | 94% (15/16) | 80% (8/10) | 100% (2/2)     |
| openai/gpt-oss-20b / v1  | 30% (12/40) | 30% (12/40)          | 67% (8/12)  | 19% (3/16)  | 10% (1/10) | 0% (0/2)       |
| openai/gpt-oss-20b / v2  | 90% (36/40) | 95% (38/40)          | 92% (11/12) | 94% (15/16) | 80% (8/10) | 100% (2/2)     |


## Failure types

| error_type          |   openai/gpt-oss-120b / v1 |   openai/gpt-oss-120b / v2 |   openai/gpt-oss-20b / v1 |   openai/gpt-oss-20b / v2 |
|:--------------------|---------------------------:|---------------------------:|--------------------------:|--------------------------:|
| grouping_error      |                          0 |                          0 |                         0 |                         1 |
| hallucinated_answer |                          2 |                          0 |                         2 |                         0 |
| unknown_column      |                         26 |                          0 |                        25 |                         0 |
| wrong_row_count     |                          0 |                          1 |                         1 |                         1 |
| wrong_values        |                          0 |                          3 |                         0 |                         2 |


## Speed and size per question

| run                      |   avg seconds |   avg prompt tokens |   avg answer tokens |
|:-------------------------|--------------:|--------------------:|--------------------:|
| openai/gpt-oss-120b / v1 |           2.3 |                 116 |               589.7 |
| openai/gpt-oss-120b / v2 |           1.4 |                 846 |               168.4 |
| openai/gpt-oss-20b / v1  |           1.9 |                 116 |               759   |
| openai/gpt-oss-20b / v2  |           1.5 |                 846 |               204.5 |

