function (keys, values, rereduce)
{
    if (rereduce)
    {
        return sum(values)
    }
    {
        /* We count one per user, not per play-event */
        return 1;
    }
}
