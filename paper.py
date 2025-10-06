class Paper:
    def __init__(self, ID, title, authors, publish_date, link, abstract, journal_ref=None):
        self.ID = ID
        self.title = title
        self.authors = authors
        self.publish_date = publish_date
        self.link = link
        self.abstract = abstract
        self.journal_ref = journal_ref

    def __str__(self) -> str:
        authors = ", ".join(self.authors)
        journal = self.journal_ref if self.journal_ref else "N/A"
        return (
            "Paper Information:\n"
            f"ID: {self.ID}\n"
            f"Title: {self.title}\n"
            f"Authors: {authors}\n"
            f"Published Date: {self.publish_date}\n"
            f"Link: {self.link}\n"
            f"Abstract: {self.abstract}\n"
            f"Journal Reference: {journal}\n"
        )

    def __repr__(self) -> str:
        return (
            "Paper("
            f"ID={self.ID!r}, "
            f"title={self.title!r}, "
            f"authors={self.authors!r}, "
            f"publish_date={self.publish_date!r}, "
            f"link={self.link!r}, "
            f"abstract={self.abstract!r}, "
            f"journal_ref={self.journal_ref!r})"
        )