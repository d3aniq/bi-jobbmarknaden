-- Avvisade annonser ska vara undantag. Fler än 1 på 10 000 betyder att
-- något i källan eller i tolkningen har ändrats, inte att datan är dålig
-- på samma sätt som förut.

select
    (select count(*) from {{ ref('rejected_ads') }}) as rejected,
    (select count(*) from {{ ref('job_ads') }})      as accepted
where (select count(*) from {{ ref('rejected_ads') }})
    > 0.0001 * (select count(*) from {{ ref('job_ads') }})
