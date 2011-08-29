from datetime import datetime

from couchdbkit.ext.django.schema import *


class Rating(DocumentSchema):
    rating    = IntegerProperty()
    timestamp = DateTimeProperty(default=datetime.utcnow)
    user      = StringProperty()


ALLOWED_RATINGS = (1, -1)

class RatingMixin(DocumentSchema):
    ratings = SchemaListProperty(Rating)

    def rate(self, rating_val, user_id):

        if user_id is None:
            raise ValueError('User must not be None')

        if rating_val not in ALLOWED_RATINGS:
            raise ValueError('Rating must be in %s' % (ALLOWED_RATINGS, ))

        rating = Rating(rating=rating_val, user=user_id)
        self.ratings = filter(lambda r: r.user != None, self.ratings)
        self.ratings = filter(lambda r: r.user != user_id, self.ratings)
        self.ratings.append(rating)
