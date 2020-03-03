import json

class DataHolderException(Exception):

    def __init__(self, message):
        self.message = message
        super(DataHolderException, self).__init__(self.message)


    def encode_to_renderable(self, dh):
        triangles = []
        for ds in dh:
            triangle = {}
            triangle["rows"] = ds.df_data.values.tolist()
            triangle["headers"] = ds.df_data.columns.values.tolist()
            triangle["name"] = ds.name
            triangle["orig_sheet_name"] = ds.orig_sheet_name
            triangle["roles"] = ds.roles
            if hasattr(dh, "card_id"):
                triangle["card_id"] = ds.card_id
            else:
                triangle["card_id"] = 0
            triangle["id"] = ds.id
            triangles.append(triangle)

        return triangles


class NoSubTrianglesException(DataHolderException):

    def __init__(self, dh):
        self.dh = self.encode_to_renderable(dh)
        self.message = "No subtriangles were found in the data holder"
        super(NoSubTrianglesException, self).__init__(self.message)


class NonNumericTriangleEntries(DataHolderException):

    def __init__(self, dh):
        self.dh = self.encode_to_renderable(dh)
        self.message = "Non numeric triangle entries detected"
        super(NonNumericTriangleEntries, self).__init__(self.message)


class DifferentlyShapedUnitTriangles(DataHolderException):

    def __init__(self, dh):
        self.dh = self.encode_to_renderable(dh)
        self.message = "The produced unit triangles do not have the same shape"
        super(DifferentlyShapedUnitTriangles, self).__init__(self.message)


class NotImplementedCaseException():
    def __init__(self):
        self.message = "This relatively rare case is not yet handled"
        super(NotImplementedCaseException, self).__init__(self.message)

class RequiredColumnsNotPresent(DataHolderException):
    def __init__(self, dh):
        self.dh = self.encode_to_renderable(dh)
        self.message = "Columns required by output template not present in triangle"
        super(RequiredColumnsNotPresent, self).__init__(self.message)


class NonpermissibleDateColumnDetected(DataHolderException):
    def __init__(self, dh):
        self.dh = self.encode_to_renderable(dh)
        self.message = "Date column with unhandled mix of input types detected"
        super(NonpermissibleDateColumnDetected, self).__init__(self.message)


class InCoherentHeadersException(DataHolderException):
    def __init__(self, dh):
        self.dh = self.encode_to_renderable(dh)
        self.message = "Headers of subtriangles not coherent"
        super(InCoherentHeadersException, self).__init__(self.message)


class NoTriangleElementsDetectedException(DataHolderException):
    def __init__(self, dh):
        self.dh = self.encode_to_renderable(dh)
        self.message = "No triangle elements were detected when stripping the triangle."
        super(NoTriangleElementsDetectedException, self).__init__(self.message)


class NothingFoundInPipelineException(DataHolderException):
    def __init__(self, dh):
        self.dh = self.encode_to_renderable(dh)
        self.message = "No triangles were detected in either triangle or table form"
        super(NothingFoundInPipelineException, self).__init__(self.message)


class UnknownColForSortingException(DataHolderException):
    def __init__(self, dh):
        self.dh = self.encode_to_renderable(dh)
        self.message = "Multiple, equally likely, unsorted date cols were found, please mark the correct one"
        super(UnknownColForSortingException, self).__init__(self.message)


class DummyColForSortingException(Exception):
    def __init__(self):
        self.message = ""
        super(DummyColForSortingException, self).__init__(self.message)
