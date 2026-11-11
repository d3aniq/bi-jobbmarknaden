select
    t.term_id,
    t.term,
    t.category,
    c.category_sort,
    c.is_core_bi,
    t.vendor,
    t.launched_year,
    t.note
from {{ ref('term_dictionary') }} t
join {{ ref('term_category') }} c using (category)
