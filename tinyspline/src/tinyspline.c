#define TINYSPLINE_EXPORT
#include "tinyspline.h"

#include <stdlib.h> /* malloc, free */
#include <math.h>   /* fabs, sqrt, acos */
#include <string.h> /* memcpy, memmove */

/* Suppress some useless MSVC warnings. */
#ifdef _MSC_VER
#pragma warning(push)
/* address of dllimport */
#pragma warning(disable:4232)
/* function not inlined */
#pragma warning(disable:4710)
/* byte padding */
#pragma warning(disable:4820)
/* meaningless deprecation */
#pragma warning(disable:4996)
/* Spectre mitigation */
#pragma warning(disable:5045)
#endif

#define INIT_OUT_BSPLINE(in, out)              \
	if ((in) != (out))                     \
		ts_int_bspline_init(out);

/*! @name Internal Structs and Functions
 *
 * Internal functions are prefixed with \e ts_int (int for internal).
 *
 * @{
 */
/**
 * Stores the private data of ::tsBSpline.
 */
struct tsBSplineImpl
{
	size_t deg; /**< Degree of B-Spline basis function. */
	size_t dim; /**< Dimensionality of the control points (2D => x, y). */
	size_t n_ctrlp; /**< Number of control points. */
	size_t n_knots; /**< Number of knots (n_ctrlp + deg + 1). */
};

/**
 * Stores the private data of ::tsDeBoorNet.
 */
struct tsDeBoorNetImpl
{
	tsReal u; /**< The evaluated knot. */
	size_t k; /**< The index [u_k, u_k+1) */
	size_t s; /**< Multiplicity of u_k. */
	size_t h; /**< Number of insertions required to obtain result. */
	size_t dim; /**< Dimensionality of the points (2D => x, y). */
	size_t n_points; /** Number of points in `points'. */
};

void
ts_int_bspline_init(tsBSpline *spline)
{
	spline->pImpl = NULL;
}

//size_t
//ts_int_bspline_sof_state(const tsBSpline *spline)
//{
//	return sizeof(struct tsBSplineImpl) +
//	       ts_bspline_sof_control_points(spline) +
//	       ts_bspline_sof_knots(spline);
//}

tsReal *
ts_int_bspline_access_ctrlp(const tsBSpline *spline)
{
	return (tsReal *) (& spline->pImpl[1]);
}

tsReal *
ts_int_bspline_access_knots(const tsBSpline *spline)
{
	return ts_int_bspline_access_ctrlp(spline) +
	       ts_bspline_len_control_points(spline);
}

tsError
ts_int_bspline_access_ctrlp_at(const tsBSpline *spline,
                               size_t index,
                               tsReal **ctrlp,
                               tsStatus *status)
{
	const size_t num = ts_bspline_num_control_points(spline);
	if (index >= num) {
		TS_RETURN_2(status, TS_INDEX_ERROR,
		            "index (%lu) >= num(control_points) (%lu)",
		            (unsigned long) index,
		            (unsigned long) num)
	}
	*ctrlp = ts_int_bspline_access_ctrlp(spline) +
	         index * ts_bspline_dimension(spline);
	TS_RETURN_SUCCESS(status)
}

tsError
ts_int_bspline_access_knot_at(const tsBSpline *spline,
                              size_t index,
                              tsReal *knot,
                              tsStatus *status)
{
	const size_t num = ts_bspline_num_knots(spline);
	if (index >= num) {
		TS_RETURN_2(status, TS_INDEX_ERROR,
		            "index (%lu) >= num(knots) (%lu)",
		            (unsigned long) index,
		            (unsigned long) num)
	}
	*knot = ts_int_bspline_access_knots(spline)[index];
	TS_RETURN_SUCCESS(status)
}

void
ts_int_deboornet_init(tsDeBoorNet *net)
{
	net->pImpl = NULL;
}

size_t
ts_int_deboornet_sof_state(const tsDeBoorNet *net)
{
	return sizeof(struct tsDeBoorNetImpl) +
	       ts_deboornet_sof_points(net) +
	       ts_deboornet_sof_result(net);
}

tsReal *
ts_int_deboornet_access_points(const tsDeBoorNet *net)
{
	return (tsReal *) (& net->pImpl[1]);
}

tsReal *
ts_int_deboornet_access_result(const tsDeBoorNet *net)
{
	if (ts_deboornet_num_result(net) == 2) {
		return ts_int_deboornet_access_points(net);
	} else {
		return ts_int_deboornet_access_points(net) +
		       /* Last point in `points`. */
		       (ts_deboornet_len_points(net) -
		        ts_deboornet_dimension(net));
	}
}
/*! @} */

/*! @name B-Spline Data
 *
 * @{
 */
size_t
ts_bspline_degree(const tsBSpline *spline)
{
	return spline->pImpl->deg;
}

size_t
ts_bspline_order(const tsBSpline *spline)
{
	return ts_bspline_degree(spline) + 1;
}

size_t
ts_bspline_dimension(const tsBSpline *spline)
{
	return spline->pImpl->dim;
}

size_t
ts_bspline_len_control_points(const tsBSpline *spline)
{
	return ts_bspline_num_control_points(spline) *
	       ts_bspline_dimension(spline);
}

size_t
ts_bspline_num_control_points(const tsBSpline *spline)
{
	return spline->pImpl->n_ctrlp;
}

size_t
ts_bspline_sof_control_points(const tsBSpline *spline)
{
	return ts_bspline_len_control_points(spline) * sizeof(tsReal);
}

//const tsReal *
//ts_bspline_control_points_ptr(const tsBSpline *spline)
//{
//	return ts_int_bspline_access_ctrlp(spline);
//}
//
//tsError
//ts_bspline_control_points(const tsBSpline *spline,
//                          tsReal **ctrlp,
//                          tsStatus *status)
//{
//	const size_t size = ts_bspline_sof_control_points(spline);
//	*ctrlp = (tsReal*) malloc(size);
//	if (!*ctrlp) TS_RETURN_0(status, TS_MALLOC, "out of memory")
//	memcpy(*ctrlp, ts_int_bspline_access_ctrlp(spline), size);
//	TS_RETURN_SUCCESS(status)
//}

//tsError
//ts_bspline_control_point_at_ptr(const tsBSpline *spline,
//                                size_t index,
//                                const tsReal **ctrlp,
//                                tsStatus *status)
//{
//	tsReal *vals;
//	tsError err;
//	TS_TRY(try, err, status)
//		TS_CALL(try, err, ts_int_bspline_access_ctrlp_at(
//		        spline, index, &vals, status))
//		*ctrlp = vals;
//	TS_CATCH(err)
//		*ctrlp = NULL;
//	TS_END_TRY_RETURN(err)
//}

//tsError
//ts_bspline_set_control_points(tsBSpline *spline,
//                              const tsReal *ctrlp,
//                              tsStatus *status)
//{
//	const size_t size = ts_bspline_sof_control_points(spline);
//	memmove(ts_int_bspline_access_ctrlp(spline), ctrlp, size);
//	TS_RETURN_SUCCESS(status)
//}

//tsError
//ts_bspline_set_control_point_at(tsBSpline *spline,
//                                size_t index,
//                                const tsReal *ctrlp,
//                                tsStatus *status)
//{
//	tsReal *to;
//	size_t size;
//	tsError err;
//	TS_TRY(try, err, status)
//		TS_CALL(try, err, ts_int_bspline_access_ctrlp_at(
//		        spline, index, &to, status))
//		size = ts_bspline_dimension(spline) * sizeof(tsReal);
//		memcpy(to, ctrlp, size);
//	TS_END_TRY_RETURN(err)
//}

size_t
ts_bspline_num_knots(const tsBSpline *spline)
{
	return spline->pImpl->n_knots;
}

size_t
ts_bspline_sof_knots(const tsBSpline *spline)
{
	return ts_bspline_num_knots(spline) * sizeof(tsReal);
}

const tsReal *
ts_bspline_knots_ptr(const tsBSpline *spline)
{
	return ts_int_bspline_access_knots(spline);
}

tsError
ts_bspline_knots(const tsBSpline *spline,
                 tsReal **knots,
                 tsStatus *status)
{
	const size_t size = ts_bspline_sof_knots(spline);
	*knots = (tsReal*) malloc(size);
	if (!*knots) TS_RETURN_0(status, TS_MALLOC, "out of memory")
	memcpy(*knots, ts_int_bspline_access_knots(spline), size);
	TS_RETURN_SUCCESS(status)
}

//tsError
//ts_bspline_knot_at(const tsBSpline *spline,
//                   size_t index,
//                   tsReal *knot,
//                   tsStatus *status)
//{
//	return ts_int_bspline_access_knot_at(spline, index, knot, status);
//}

//tsError
//ts_bspline_set_knots(tsBSpline *spline,
//                     const tsReal *knots,
//                     tsStatus *status)
//{
//	const size_t size = ts_bspline_sof_knots(spline);
//	const size_t num_knots = ts_bspline_num_knots(spline);
//	const size_t order = ts_bspline_order(spline);
//	size_t idx, mult;
//	tsReal lst_knot, knot;
//	lst_knot = knots[0];
//	mult = 1;
//	for (idx = 1; idx < num_knots; idx++) {
//		knot = knots[idx];
//		if (ts_knots_equal(lst_knot, knot)) {
//			mult++;
//		} else if (lst_knot > knot) {
//			TS_RETURN_1(status, TS_KNOTS_DECR,
//			            "decreasing knot vector at index: %lu",
//			            (unsigned long) idx)
//		} else {
//			mult = 0;
//		}
//		if (mult > order) {
//			TS_RETURN_3(status, TS_MULTIPLICITY,
//			            "mult(%f) (%lu) > order (%lu)",
//			            knot, (unsigned long) mult,
//			            (unsigned long) order)
//		}
//		lst_knot = knot;
//	}
//	memmove(ts_int_bspline_access_knots(spline), knots, size);
//	TS_RETURN_SUCCESS(status)
//}

//tsError
//ts_bspline_set_knots_varargs(tsBSpline *spline,
//                             tsStatus *status,
//                             tsReal knot0,
//                             double knot1,
//                             ...)
//{
//	tsReal *values = NULL;
//	va_list argp;
//	size_t idx;
//	tsError err;
//
//	TS_TRY(try, err, status)
//		TS_CALL(try, err, ts_bspline_knots(
//		        spline, &values, status))
//
//		values[0] = knot0;
//		values[1] = (tsReal) knot1;
//		va_start(argp, knot1);
//		for (idx = 2; idx < ts_bspline_num_knots(spline); idx++)
//			values[idx] = (tsReal) va_arg(argp, double);
//		va_end(argp);
//
//		TS_CALL(try, err, ts_bspline_set_knots(
//		        spline, values, status))
//	TS_FINALLY
//		if (values) free(values);
//	TS_END_TRY_RETURN(err)
//}

//tsError
//ts_bspline_set_knot_at(tsBSpline *spline,
//                       size_t index,
//                       tsReal knot,
//                       tsStatus *status)
//{
//	tsError err;
//	tsReal *knots = NULL;
//	/* This is only for initialization. */
//	tsReal oldKnot = ts_int_bspline_access_knots(spline)[0];
//	TS_TRY(try, err, status)
//		TS_CALL(try, err, ts_int_bspline_access_knot_at(
//		        spline, index, &oldKnot, status))
//		/* knots must be set after reading oldKnot because the catch
//		 * block assumes that oldKnot contains the correct value if
//		 * knots is not NULL. */
//		knots = ts_int_bspline_access_knots(spline);
//		knots[index] = knot;
//		TS_CALL(try, err, ts_bspline_set_knots(
//		        spline, knots, status))
//	TS_CATCH(err)
//		/* If knots is not NULL, oldKnot contains the correct value. */
//		if (knots) knots[index] = oldKnot;
//	TS_END_TRY_RETURN(err)
//}
/*! @} */

/*! @name B-Spline Initialization
 *
 * @{
 */
tsBSpline
ts_bspline_init(void)
{
	tsBSpline spline;
	ts_int_bspline_init(&spline);
	return spline;
}

tsError
ts_int_bspline_generate_knots(const tsBSpline *spline,
                              tsBSplineType type,
                              tsStatus *status)
{
	const size_t n_knots = ts_bspline_num_knots(spline);
	const size_t deg = ts_bspline_degree(spline);
	const size_t order = ts_bspline_order(spline);
	tsReal fac; /**< Factor used to calculate the knot values. */
	size_t i; /**< Used in for loops. */
	tsReal *knots; /**< Pointer to the knots of \p _result_. */

	/* order >= 1 implies 2*order >= 2 implies n_knots >= 2 */
	if (type == TS_BEZIERS && n_knots % order != 0) {
		TS_RETURN_2(status, TS_NUM_KNOTS,
		            "num(knots) (%lu) %% order (%lu) != 0",
		            (unsigned long) n_knots, (unsigned long) order)
	}

	knots = ts_int_bspline_access_knots(spline);

	if (type == TS_OPENED) {
		knots[0] = TS_DOMAIN_DEFAULT_MIN; /* n_knots >= 2 */
		fac = (TS_DOMAIN_DEFAULT_MAX - TS_DOMAIN_DEFAULT_MIN)
		      / (n_knots - 1); /* n_knots >= 2 */
		for (i = 1; i < n_knots-1; i++)
			knots[i] = TS_DOMAIN_DEFAULT_MIN + i*fac;
		knots[i] = TS_DOMAIN_DEFAULT_MAX; /* n_knots >= 2 */
	} else if (type == TS_CLAMPED) {
		/* n_knots >= 2*order == 2*(deg+1) == 2*deg + 2 > 2*deg - 1 */
		fac = (TS_DOMAIN_DEFAULT_MAX - TS_DOMAIN_DEFAULT_MIN)
		      / (n_knots - 2*deg - 1);
		ts_arr_fill(knots, order, TS_DOMAIN_DEFAULT_MIN);
		for (i = order ;i < n_knots-order; i++)
			knots[i] = TS_DOMAIN_DEFAULT_MIN + (i-deg)*fac;
		ts_arr_fill(knots + i, order, TS_DOMAIN_DEFAULT_MAX);
	} else if (type == TS_BEZIERS) {
		/* n_knots >= 2*order implies n_knots/order >= 2 */
		fac = (TS_DOMAIN_DEFAULT_MAX - TS_DOMAIN_DEFAULT_MIN)
		      / (n_knots/order - 1);
		ts_arr_fill(knots, order, TS_DOMAIN_DEFAULT_MIN);
		for (i = order; i < n_knots-order; i += order)
			ts_arr_fill(knots + i,
			            order,
			            TS_DOMAIN_DEFAULT_MIN + (i/order)*fac);
		ts_arr_fill(knots + i, order, TS_DOMAIN_DEFAULT_MAX);
	}
	TS_RETURN_SUCCESS(status)
}

tsError
ts_bspline_new(size_t num_control_points,
               size_t dimension,
               size_t degree,
               tsBSplineType type,
               tsBSpline *spline,
               tsStatus *status)
{
	const size_t order = degree + 1;
	const size_t num_knots = num_control_points + order;
	const size_t len_ctrlp = num_control_points * dimension;

	const size_t sof_real = sizeof(tsReal);
	const size_t sof_impl = sizeof(struct tsBSplineImpl);
	const size_t sof_ctrlp_vec = len_ctrlp * sof_real;
	const size_t sof_knots_vec = num_knots * sof_real;
	const size_t sof_spline = sof_impl + sof_ctrlp_vec + sof_knots_vec;
	tsError err;

	ts_int_bspline_init(spline);

	if (dimension < 1) {
		TS_RETURN_0(status, TS_DIM_ZERO, "unsupported dimension: 0")
	}
	if (num_knots > TS_MAX_NUM_KNOTS) {
		TS_RETURN_2(status, TS_NUM_KNOTS,
		            "unsupported number of knots: %lu > %i",
		            (unsigned long) num_knots, TS_MAX_NUM_KNOTS)
	}
	if (degree >= num_control_points) {
		TS_RETURN_2(status, TS_DEG_GE_NCTRLP,
		            "degree (%lu) >= num(control_points) (%lu)",
		            (unsigned long) degree,
		            (unsigned long) num_control_points)
	}

	spline->pImpl = (struct tsBSplineImpl *) malloc(sof_spline);
	if (!spline->pImpl) TS_RETURN_0(status, TS_MALLOC, "out of memory")

	spline->pImpl->deg = degree;
	spline->pImpl->dim = dimension;
	spline->pImpl->n_ctrlp = num_control_points;
	spline->pImpl->n_knots = num_knots;

	TS_TRY(try, err, status)
		TS_CALL(try, err, ts_int_bspline_generate_knots(
		        spline, type, status))
	TS_CATCH(err)
		ts_bspline_free(spline);
	TS_END_TRY_RETURN(err)
}

void
ts_bspline_free(tsBSpline *spline)
{
	if (spline->pImpl) free(spline->pImpl);
	ts_int_bspline_init(spline);
}
/*! @} */

/*! @name De Boor Net Data
 *
 * @{
 */
tsReal
ts_deboornet_knot(const tsDeBoorNet *net)
{
	return net->pImpl->u;
}

size_t
ts_deboornet_index(const tsDeBoorNet *net)
{
	return net->pImpl->k;
}

size_t
ts_deboornet_multiplicity(const tsDeBoorNet *net)
{
	return net->pImpl->s;
}

size_t
ts_deboornet_num_insertions(const tsDeBoorNet *net)
{
	return net->pImpl->h;
}

size_t
ts_deboornet_dimension(const tsDeBoorNet *net)
{
	return net->pImpl->dim;
}

size_t
ts_deboornet_len_points(const tsDeBoorNet *net)
{
	return ts_deboornet_num_points(net) *
	       ts_deboornet_dimension(net);
}

size_t
ts_deboornet_num_points(const tsDeBoorNet *net)
{
	return net->pImpl->n_points;
}

size_t
ts_deboornet_sof_points(const tsDeBoorNet *net)
{
	return ts_deboornet_len_points(net) * sizeof(tsReal);
}

const tsReal *
ts_deboornet_points_ptr(const tsDeBoorNet *net)
{
	return ts_int_deboornet_access_points(net);
}

tsError
ts_deboornet_points(const tsDeBoorNet *net,
                    tsReal **points,
                    tsStatus *status)
{
	const size_t size = ts_deboornet_sof_points(net);
	*points = (tsReal*) malloc(size);
	if (!*points) TS_RETURN_0(status, TS_MALLOC, "out of memory")
	memcpy(*points, ts_int_deboornet_access_points(net), size);
	TS_RETURN_SUCCESS(status)
}

size_t
ts_deboornet_len_result(const tsDeBoorNet *net)
{
	return ts_deboornet_num_result(net) *
	       ts_deboornet_dimension(net);
}

size_t
ts_deboornet_num_result(const tsDeBoorNet *net)
{
	return ts_deboornet_num_points(net) == 2 ? 2 : 1;
}

size_t
ts_deboornet_sof_result(const tsDeBoorNet *net)
{
	return ts_deboornet_len_result(net) * sizeof(tsReal);
}

const tsReal *
ts_deboornet_result_ptr(const tsDeBoorNet *net)
{
	return ts_int_deboornet_access_result(net);
}

tsError
ts_deboornet_result(const tsDeBoorNet *net,
                    tsReal **result,
                    tsStatus *status)
{
	const size_t size = ts_deboornet_sof_result(net);
	*result = (tsReal*) malloc(size);
	if (!*result) TS_RETURN_0(status, TS_MALLOC, "out of memory")
	memcpy(*result, ts_int_deboornet_access_result(net), size);
	TS_RETURN_SUCCESS(status)
}
/*! @} */

/*! @name De Boor Net Initialization
 *
 * @{
 */
tsDeBoorNet
ts_deboornet_init(void)
{
	tsDeBoorNet net;
	ts_int_deboornet_init(&net);
	return net;
}

tsError
ts_int_deboornet_new(const tsBSpline *spline,
                     tsDeBoorNet *net,
                     tsStatus *status)
{
	const size_t dim = ts_bspline_dimension(spline);
	const size_t deg = ts_bspline_degree(spline);
	const size_t order = ts_bspline_order(spline);
	const size_t num_points = (size_t)(order * (order+1) * 0.5f);
	/* Handle `order == 1' which generates too few points. */
	const size_t fixed_num_points = num_points < 2 ? 2 : num_points;

	const size_t sof_real = sizeof(tsReal);
	const size_t sof_impl = sizeof(struct tsDeBoorNetImpl);
	const size_t sof_points_vec = fixed_num_points * dim * sof_real;
	const size_t sof_net = sof_impl + sof_points_vec;

	net->pImpl = (struct tsDeBoorNetImpl *) malloc(sof_net);
	if (!net->pImpl) TS_RETURN_0(status, TS_MALLOC, "out of memory")

	net->pImpl->u = 0.f;
	net->pImpl->k = 0;
	net->pImpl->s = 0;
	net->pImpl->h = deg;
	net->pImpl->dim = dim;
	net->pImpl->n_points = fixed_num_points;
	TS_RETURN_SUCCESS(status)
}

void
ts_deboornet_free(tsDeBoorNet *net)
{
	if (net->pImpl) free(net->pImpl);
	ts_int_deboornet_init(net);
}

//tsError
//ts_deboornet_copy(const tsDeBoorNet *src,
//                  tsDeBoorNet *dest,
//                  tsStatus *status)
//{
//	size_t size;
//	if (src == dest) TS_RETURN_SUCCESS(status)
//	ts_int_deboornet_init(dest);
//	size = ts_int_deboornet_sof_state(src);
//	dest->pImpl = (struct tsDeBoorNetImpl *) malloc(size);
//	if (!dest->pImpl) TS_RETURN_0(status, TS_MALLOC, "out of memory")
//	memcpy(dest->pImpl, src->pImpl, size);
//	TS_RETURN_SUCCESS(status)
//}

//void
//ts_deboornet_move(tsDeBoorNet *src,
//                  tsDeBoorNet *dest)
//{
//	if (src == dest) return;
//	dest->pImpl = src->pImpl;
//	ts_int_deboornet_init(src);
//}
///*! @} */

/*! @name Interpolation and Approximation Functions
 *
 * @{
 */
tsError
ts_int_cubic_point(const tsReal *point,
                   size_t dim,
                   tsBSpline *spline,
                   tsStatus *status)
{
	const size_t size = dim * sizeof(tsReal);
	tsReal *ctrlp = NULL;
	size_t i;
	tsError err;
	TS_CALL_ROE(err, ts_bspline_new(
	            4, dim, 3,
	            TS_CLAMPED, spline, status))
	ctrlp = ts_int_bspline_access_ctrlp(spline);
	for (i = 0; i < 4; i++) {
		memcpy(ctrlp + i*dim,
		       point,
		       size);
	}
	TS_RETURN_SUCCESS(status)
}

tsError
ts_int_thomas_algorithm(const tsReal *a,
                        const tsReal *b,
                        const tsReal *c,
                        size_t num,
                        size_t dim,
                        tsReal *d,
                        tsStatus *status)
{
	size_t i, j, k, l;
	tsReal m, *cc = NULL;
	tsError err;

	if (dim == 0) {
		TS_RETURN_0(status, TS_DIM_ZERO,
		            "unsupported dimension: 0")
	}
	if (num <= 1) {
		TS_RETURN_1(status, TS_NUM_POINTS,
		            "num(points) (%lu) <= 1",
		            (unsigned long) num)
	}
	cc = (tsReal *) malloc(num * sizeof(tsReal));
	if (!cc) TS_RETURN_0(status, TS_MALLOC, "out of memory")

	TS_TRY(try, err, status)
		/* Forward sweep. */
		if (fabs(b[0]) <= fabs(c[0])) {
			TS_THROW_2(try, err, status, TS_NO_RESULT,
			           "error: |%f| <= |%f|", b[0], c[0])
		}
		/* |b[i]| > |c[i]| implies that |b[i]| > 0. Thus, the following
		 * statements cannot evaluate to division by zero.*/
		cc[0] = c[0] / b[0];
		for (i = 0; i < dim; i++)
			d[i] = d[i] / b[0];
		for (i = 1; i < num; i++) {
			if (fabs(b[i]) <= fabs(a[i]) + fabs(c[i])) {
				TS_THROW_3(try, err, status, TS_NO_RESULT,
				           "error: |%f| <= |%f| + |%f|",
				           b[i], a[i], c[i])
			}
			/* |a[i]| < |b[i]| and cc[i - 1] < 1. Therefore, the
			 * following statement cannot evaluate to division by
			 * zero. */
			m = 1.f / (b[i] - a[i] * cc[i - 1]);
			/* |b[i]| > |a[i]| + |c[i]| implies that there must be
			 * an eps > 0 such that |b[i]| = |a[i]| + |c[i]| + eps.
			 * Even if |a[i]| is 0 (by which the result of the
			 * following statement becomes maximum), |c[i]| is less
			 * than |b[i]| by an amount of eps. By substituting the
			 * previous and the following statements (under the
			 * assumption that |a[i]| is 0), we obtain c[i] / b[i],
			 * which must be less than 1. */
			cc[i] = c[i] * m;
			for (j = 0; j < dim; j++) {
				k = i * dim + j;
				l = (i-1) * dim + j;
				d[k] = (d[k] - a[i] * d[l]) * m;
			}
		}

		/* Back substitution. */
		for (i = num-1; i > 0; i--) {
			for (j = 0; j < dim; j++) {
				k = (i-1) * dim + j;
				l = i * dim + j;
				d[k] -= cc[i-1] * d[l];
			}
		}
	TS_FINALLY
		free(cc);
	TS_END_TRY_RETURN(err)
}

tsError
ts_int_relaxed_uniform_cubic_bspline(const tsReal *points,
                                     size_t n,
                                     size_t dim,
                                     tsBSpline *spline,
                                     tsStatus *status)
{
	const size_t order = 4;    /**< Order of spline to interpolate. */
	const tsReal as = 1.f/6.f; /**< The value 'a sixth'. */
	const tsReal at = 1.f/3.f; /**< The value 'a third'. */
	const tsReal tt = 2.f/3.f; /**< The value 'two third'. */
	size_t sof_ctrlp;          /**< Size of a single control point. */
	const tsReal* b = points;  /**< Array of the b values. */
	tsReal* s;                 /**< Array of the s values. */
	size_t i, d;               /**< Used in for loops */
	size_t j, k, l;            /**< Used as temporary indices. */
	tsReal *ctrlp; /**< Pointer to the control points of \p _spline_. */
	tsError err;

	/* input validation */
	if (dim == 0)
		TS_RETURN_0(status, TS_DIM_ZERO, "unsupported dimension: 0")
	if (n <= 1) {
		TS_RETURN_1(status, TS_NUM_POINTS,
		            "num(points) (%lu) <= 1",
		            (unsigned long) n)
	}
	/* in the following n >= 2 applies */

	sof_ctrlp = dim * sizeof(tsReal); /* dim > 0 implies sof_ctrlp > 0 */

	s = NULL;
	TS_TRY(try, err, status)
		/* n >= 2 implies n-1 >= 1 implies (n-1)*4 >= 4 */
		TS_CALL(try, err, ts_bspline_new(
		        (n-1) * 4, dim, order - 1,
		        TS_BEZIERS, spline, status))
		ctrlp = ts_int_bspline_access_ctrlp(spline);

		s = (tsReal*) malloc(n * sof_ctrlp);
		if (!s) {
			TS_THROW_0(try, err, status, TS_MALLOC,
			           "out of memory")
		}

		/* set s_0 to b_0 and s_n = b_n */
		memcpy(s, b, sof_ctrlp);
		memcpy(s + (n-1)*dim, b + (n-1)*dim, sof_ctrlp);

		/* set s_i = 1/6*b_{i-1} + 2/3*b_{i} + 1/6*b_{i+1}*/
		for (i = 1; i < n-1; i++) {
			for (d = 0; d < dim; d++) {
				j = (i-1)*dim+d;
				k = i*dim+d;
				l = (i+1)*dim+d;
				s[k] = as * b[j];
				s[k] += tt * b[k];
				s[k] += as * b[l];
			}
		}

		/* create beziers from b and s */
		for (i = 0; i < n-1; i++) {
			for (d = 0; d < dim; d++) {
				j = i*dim+d;
				k = i*4*dim+d;
				l = (i+1)*dim+d;
				ctrlp[k] = s[j];
				ctrlp[k+dim] = tt*b[j] + at*b[l];
				ctrlp[k+2*dim] = at*b[j] + tt*b[l];
				ctrlp[k+3*dim] = s[l];
			}
		}
	TS_CATCH(err)
		ts_bspline_free(spline);
	TS_FINALLY
		if (s)
			free(s);
	TS_END_TRY_RETURN(err)
}

tsError
ts_bspline_interpolate_cubic_natural(const tsReal *points,
                                     size_t num_points,
                                     size_t dimension,
                                     tsBSpline *spline,
                                     tsStatus *status)
{
	const size_t sof_ctrlp = dimension * sizeof(tsReal);
	const size_t len_points = num_points * dimension;
	const size_t num_int_points = num_points - 2;
	const size_t len_int_points = num_int_points * dimension;
	tsReal *buffer, *a, *b, *c, *d;
	size_t i, j, k, l;
	tsError err;

	ts_int_bspline_init(spline);
	if (num_points == 0)
		TS_RETURN_0(status, TS_NUM_POINTS, "num(points) == 0")
	if (num_points == 1)
	{
		TS_CALL_ROE(err, ts_int_cubic_point(
		            points, dimension, spline, status))
		TS_RETURN_SUCCESS(status)
	}
	if (num_points == 2)
	{
		return ts_int_relaxed_uniform_cubic_bspline(
			points, num_points, dimension, spline, status);
	}
	/* `num_points` >= 3 */
	buffer = NULL;
	TS_TRY(try, err, status)
		buffer = (tsReal *) malloc(
			/* `a', `b', `c' (note that `c' is equal to `a') */
			2 * num_int_points * sizeof(tsReal) +
			/* At first: `d' Afterwards: The result of the thomas
			 * algorithm including the first and last point to be
			 * interpolated. */
			num_points * dimension * sizeof(tsReal));
		if (!buffer)
		{
			TS_THROW_0(try, err, status, TS_MALLOC,
			           "out of memory")
		}
		/* The system of linear equations is taken from:
		 *     http://www.bakoma-tex.com/doc/generic/pst-bspline/
		 *     pst-bspline-doc.pdf */
		a = c = buffer;
		ts_arr_fill(a, num_int_points, 1);
		b = a + num_int_points;
		ts_arr_fill(b, num_int_points, 4);
		d = b + num_int_points /* shift to the beginning of `d' */
		      + dimension; /* make space for the first point */
		/* 6 * S_{i+1} */
		for (i = 0; i < num_int_points; i++)
		{
			for (j = 0; j < dimension; j++)
			{
				k = i * dimension + j;
				l = (i+1) * dimension + j;
				d[k] = 6 * points[l];
			}
		}
		for (i = 0; i < dimension; i++)
		{
			/* 6 * S_{1} - S_{0} */
			d[i] -= points[i];
			/* 6 * S_{n-1} - S_{n} */
			k = len_int_points - (i+1);
			l = len_points - (i+1);
			d[k] -= points[l];
		}
		/* The Thomas algorithm requires at least two points. Hence,
		 * `num_int_points` == 1 must be handled separately (let's call
		 * it "Mini Thomas"). */
		if (num_int_points == 1)
		{
			for (i = 0; i < dimension; i++)
				d[i] *= (tsReal) 0.25f;
		}
		else
		{
			TS_CALL(try, err, ts_int_thomas_algorithm(
			        a, b, c, num_int_points, dimension, d,
			        status))
		}
		memcpy(d - dimension, points, sof_ctrlp);
		memcpy(d + num_int_points * dimension,
		       points + (num_points-1) * dimension,
		       sof_ctrlp);
		TS_CALL(try, err, ts_int_relaxed_uniform_cubic_bspline(
		        d - dimension, num_points, dimension, spline, status))
	TS_CATCH(err)
		ts_bspline_free(spline);
	TS_FINALLY
		if (buffer) free(buffer);
	TS_END_TRY_RETURN(err)
}

/*! @name Query Functions
 *
 * @{
 */
tsError
ts_int_bspline_find_knot(const tsBSpline *spline,
                         tsReal *knot, /* in: knot; out: actual knot */
                         size_t *idx,  /* out: index of `knot' */
                         size_t *mult, /* out: multiplicity of `knot' */
                         tsStatus *status)
{
	const size_t deg = ts_bspline_degree(spline);
	const size_t num_knots = ts_bspline_num_knots(spline);
	const tsReal *knots = ts_int_bspline_access_knots(spline);
	tsReal min, max;
	size_t low, high;

	ts_bspline_domain(spline, &min, &max);
	if (*knot < min) {
		/* Avoid infinite loop (issue #222) */
		if (ts_knots_equal(*knot, min)) *knot = min;
		else {
			TS_RETURN_2(status, TS_U_UNDEFINED,
			            "knot (%f) < min(domain) (%f)",
			            *knot, min)
		}
	}
	else if (*knot > max && !ts_knots_equal(*knot, max)) {
		TS_RETURN_2(status, TS_U_UNDEFINED,
		            "knot (%f) > max(domain) (%f)",
		            *knot, max)
	}

	/* Based on 'The NURBS Book' (Les Piegl and Wayne Tiller). */
	if (ts_knots_equal(*knot, knots[num_knots - 1])) {
		*idx = num_knots - 1;
	} else {
		low = 0;
		high = num_knots - 1;
		*idx = (low+high) / 2;
		while (*knot < knots[*idx] || *knot >= knots[*idx + 1]) {
			if (*knot < knots[*idx])
				high = *idx;
			else
				low = *idx;
			*idx = (low+high) / 2;
		}
	}

	/* Handle floating point errors. */
	while (*idx < num_knots - 1 && /* there is a next knot */
	       ts_knots_equal(*knot, knots[*idx + 1])) {
		(*idx)++;
	}
	if (ts_knots_equal(*knot, knots[*idx]))
		*knot = knots[*idx]; /* set actual knot */

	/* Calculate knot's multiplicity. */
	for (*mult = deg + 1; *mult > 0 ; (*mult)--) {
		if (ts_knots_equal(*knot, knots[*idx - (*mult-1)]))
			break;
	}

	TS_RETURN_SUCCESS(status)
}

tsError
ts_int_bspline_eval_woa(const tsBSpline *spline,
                        tsReal u,
                        tsDeBoorNet *net,
                        tsStatus *status)
{
	const size_t deg = ts_bspline_degree(spline);
	const size_t order = ts_bspline_order(spline);
	const size_t dim = ts_bspline_dimension(spline);
	const size_t num_knots = ts_bspline_num_knots(spline);
	const size_t sof_ctrlp = dim * sizeof(tsReal);

	const tsReal *ctrlp = ts_int_bspline_access_ctrlp(spline);
	const tsReal *knots = ts_int_bspline_access_knots(spline);
	tsReal *points = NULL;  /**< Pointer to the points of \p net. */

	size_t k;        /**< Index of \p u. */
	size_t s;        /**< Multiplicity of \p u. */

	size_t from;     /**< Offset used to copy values. */
	size_t fst;      /**< First affected control point, inclusive. */
	size_t lst;      /**< Last affected control point, inclusive. */
	size_t N;        /**< Number of affected control points. */

	/* The following indices are used to create the DeBoor net. */
	size_t lidx;     /**< Current left index. */
	size_t ridx;     /**< Current right index. */
	size_t tidx;     /**< Current to index. */
	size_t r, i, d;  /**< Used in for loop. */
	tsReal ui;       /**< Knot value at index i. */
	tsReal a, a_hat; /**< Weighting factors of control points. */

	tsError err;

	points = ts_int_deboornet_access_points(net);

	/* 1. Find index k such that u is in between [u_k, u_k+1).
	 * 2. Setup already known values.
	 * 3. Decide by multiplicity of u how to calculate point P(u). */

	/* 1. */
	k = s = 0;
	TS_CALL_ROE(err, ts_int_bspline_find_knot(
	            spline, &u, &k, &s, status))

	/* 2. */
	net->pImpl->u = u;
	net->pImpl->k = k;
	net->pImpl->s = s;
	net->pImpl->h = deg < s ? 0 : deg-s; /* prevent underflow */

	/* 3. (by 1. s <= order)
	 *
	 * 3a) Check for s = order.
	 *     Take the two points k-s and k-s + 1. If one of
	 *     them doesn't exist, take only the other.
	 * 3b) Use de boor algorithm to find point P(u). */
	if (s == order) {
		/* only one of the two control points exists */
		if (k == deg || /* only the first */
		    k == num_knots - 1) { /* only the last */
			from = k == deg ? 0 : (k-s) * dim;
			net->pImpl->n_points = 1;
			memcpy(points, ctrlp + from, sof_ctrlp);
		} else {
			from = (k-s) * dim;
			net->pImpl->n_points = 2;
			memcpy(points, ctrlp + from, 2 * sof_ctrlp);
		}
	} else { /* by 3a) s <= deg (order = deg+1) */
		fst = k-deg; /* by 1. k >= deg */
		lst = k-s; /* s <= deg <= k */
		N = lst-fst + 1; /* lst <= fst implies N >= 1 */

		net->pImpl->n_points = (size_t)(N * (N+1) * 0.5f);

		/* copy initial values to output */
		memcpy(points, ctrlp + fst*dim, N * sof_ctrlp);

		lidx = 0;
		ridx = dim;
		tidx = N*dim; /* N >= 1 implies tidx > 0 */
		r = 1;
		for (;r <= ts_deboornet_num_insertions(net); r++) {
			i = fst + r;
			for (; i <= lst; i++) {
				ui = knots[i];
				a = (ts_deboornet_knot(net) - ui) /
					(knots[i+deg-r+1] - ui);
				a_hat = 1.f-a;

				for (d = 0; d < dim; d++) {
					points[tidx++] =
						a_hat * points[lidx++] +
						a     * points[ridx++];
				}
			}
			lidx += dim;
			ridx += dim;
		}
	}
	TS_RETURN_SUCCESS(status)
}

//tsError
//ts_bspline_eval(const tsBSpline *spline,
//                tsReal knot,
//                tsDeBoorNet *net,
//                tsStatus *status)
//{
//	tsError err;
//	ts_int_deboornet_init(net);
//	TS_TRY(try, err, status)
//		TS_CALL(try, err, ts_int_deboornet_new(
//		        spline, net, status))
//		TS_CALL(try, err, ts_int_bspline_eval_woa(
//		        spline, knot, net, status))
//	TS_CATCH(err)
//		ts_deboornet_free(net);
//	TS_END_TRY_RETURN(err)
//}

tsError
ts_bspline_eval_all(const tsBSpline *spline,
                    const tsReal *knots,
                    size_t num,
                    tsReal **points,
                    tsStatus *status)
{
	const size_t dim = ts_bspline_dimension(spline);
	const size_t sof_point = dim * sizeof(tsReal);
	const size_t sof_points = num * sof_point;
	tsDeBoorNet net = ts_deboornet_init();
	tsReal *result;
	size_t i;
	tsError err;
	TS_TRY(try, err, status)
		*points = (tsReal *) malloc(sof_points);
		if (!*points) {
			TS_THROW_0(try, err, status, TS_MALLOC,
			           "out of memory")
		}
		TS_CALL(try, err, ts_int_deboornet_new(
		        spline,&net, status))
		for (i = 0; i < num; i++) {
			TS_CALL(try, err, ts_int_bspline_eval_woa(
			        spline, knots[i], &net, status))
			result = ts_int_deboornet_access_result(&net);
			memcpy((*points) + i * dim, result, sof_point);
		}
	TS_CATCH(err)
		if (*points)
			free(*points);
		*points = NULL;
	TS_FINALLY
		ts_deboornet_free(&net);
	TS_END_TRY_RETURN(err)
}

tsError
ts_bspline_sample(const tsBSpline *spline,
                  size_t num,
                  tsReal **points,
                  size_t *actual_num,
                  tsStatus *status)
{
	tsError err;
	tsReal *knots;

	num = num == 0 ? 100 : num;
	*actual_num = num;
	knots = (tsReal *) malloc(num * sizeof(tsReal));
	if (!knots) {
		*points = NULL;
		TS_RETURN_0(status, TS_MALLOC, "out of memory")
	}
	ts_bspline_uniform_knot_seq(spline, num, knots);
	TS_TRY(try, err, status)
		TS_CALL(try, err, ts_bspline_eval_all(
		        spline, knots, num, points, status))
	TS_FINALLY
		free(knots);
	TS_END_TRY_RETURN(err)
}

tsError
ts_bspline_bisect(const tsBSpline *spline,
                  tsReal value,
                  tsReal epsilon,
                  int persnickety,
                  size_t index,
                  int ascending,
                  size_t max_iter,
                  tsDeBoorNet *net,
                  tsStatus *status)
{
	tsError err;
	const size_t dim = ts_bspline_dimension(spline);
	const tsReal eps = (tsReal) fabs(epsilon);
	size_t i = 0;
	tsReal dist = 0;
	tsReal min, max, mid;
	tsReal *P;

	ts_int_deboornet_init(net);

	if (dim < index) {
		TS_RETURN_2(status, TS_INDEX_ERROR,
		            "dimension (%lu) <= index (%lu)",
		            (unsigned long) dim,
		            (unsigned long) index)
	}
	if(max_iter == 0)
		TS_RETURN_0(status, TS_NO_RESULT, "0 iterations")

	ts_bspline_domain(spline, &min, &max);
	TS_TRY(try, err, status)
		TS_CALL(try, err, ts_int_deboornet_new(
		        spline, net, status))
		do {
			mid = (tsReal) ((min + max) / 2.0);
			TS_CALL(try, err, ts_int_bspline_eval_woa(
			        spline, mid, net, status))
			P = ts_int_deboornet_access_result(net);
			dist = ts_distance(&P[index], &value, 1);
			if (dist <= eps)
				TS_RETURN_SUCCESS(status)
			if (ascending) {
				if (P[index] < value)
					min = mid;
				else
					max = mid;
			} else {
				if (P[index] < value)
					max = mid;
				else
					min = mid;
			}
		} while (i++ < max_iter);
		if (persnickety) {
			TS_THROW_1(try, err, status, TS_NO_RESULT,
			           "maximum iterations (%lu) exceeded",
			           (unsigned long) max_iter)
		}
	TS_CATCH(err)
		ts_deboornet_free(net);
	TS_END_TRY_RETURN(err)
}

void ts_bspline_domain(const tsBSpline *spline,
                       tsReal *min,
                       tsReal *max)
{
	*min = ts_int_bspline_access_knots(spline)
		[ts_bspline_degree(spline)];
	*max = ts_int_bspline_access_knots(spline)
		[ts_bspline_num_knots(spline) - ts_bspline_order(spline)];
}

void
ts_bspline_uniform_knot_seq(const tsBSpline *spline,
                            size_t num,
                            tsReal *knots)
{
	size_t i;
	tsReal min, max;
	if (num == 0) return;
	ts_bspline_domain(spline, &min, &max);
	for (i = 0; i < num; i++) {
		knots[i] = max - min;
		knots[i] *= (tsReal) i / (num - 1);
		knots[i] += min;
	}
	/* Set `knots[0]` after `knots[num - 1]` to ensure
	   that `knots[0] = min` if `num` is `1'. */
	knots[num - 1] = max;
	knots[0] = min;
}

/*! @name Vector Math
 * @{
 */
//void
//ts_vec2_init(tsReal *out,
//             tsReal x,
//             tsReal y)
//{
//	out[0] = x;
//	out[1] = y;
//}

//void
//ts_vec3_init(tsReal *out,
//             tsReal x,
//             tsReal y,
//             tsReal z)
//{
//	out[0] = x;
//	out[1] = y;
//	out[2] = z;
//}

//void
//ts_vec4_init(tsReal *out,
//             tsReal x,
//             tsReal y,
//             tsReal z,
//             tsReal w)
//{
//	out[0] = x;
//	out[1] = y;
//	out[2] = z;
//	out[3] = w;
//}

//void
//ts_vec2_set(tsReal *out,
//            const tsReal *x,
//            size_t dim)
//{
//	const size_t n = dim > 2 ? 2 : dim;
//	memmove(out, x, n * sizeof(tsReal));
//	if (dim < 2)
//		ts_arr_fill(out + dim, 2 - dim, (tsReal) 0.0);
//}
//
//void
//ts_vec3_set(tsReal *out,
//            const tsReal *x,
//            size_t dim)
//{
//	const size_t n = dim > 3 ? 3 : dim;
//	memmove(out, x, n * sizeof(tsReal));
//	if (dim < 3)
//		ts_arr_fill(out + dim, 3 - dim, (tsReal) 0.0);
//}
//
//void
//ts_vec4_set(tsReal *out,
//            const tsReal *x,
//            size_t dim)
//{
//	const size_t n = dim > 4 ? 4 : dim;
//	memmove(out, x, n * sizeof(tsReal));
//	if (dim < 4)
//		ts_arr_fill(out + dim, 4 - dim, (tsReal) 0.0);
//}
//
//void
//ts_vec_add(const tsReal *x,
//           const tsReal *y,
//           size_t dim,
//           tsReal *out)
//{
//	size_t i;
//	for (i = 0; i < dim; i++)
//		out[i] = x[i] + y[i];
//}
//
//void
//ts_vec_sub(const tsReal *x,
//           const tsReal *y,
//           size_t dim,
//           tsReal *out)
//{
//	size_t i;
//	if (x == y) {
//		/* More stable version. */
//		ts_arr_fill(out, dim, (tsReal) 0.0);
//		return;
//	}
//	for (i = 0; i < dim; i++)
//		out[i] = x[i] - y[i];
//}
//
//tsReal
//ts_vec_dot(const tsReal *x,
//           const tsReal *y,
//           size_t dim)
//{
//	size_t i;
//	tsReal dot = 0;
//	for (i = 0; i < dim; i++)
//		dot += x[i] * y[i];
//	return dot;
//}
//
//tsReal
//ts_vec_angle(const tsReal *x,
//             const tsReal *y,
//             tsReal *buf,
//             size_t dim)
//{
//	const tsReal *x_norm, *y_norm;
//	if (buf) {
//		ts_vec_norm(x, dim, buf);
//		ts_vec_norm(y, dim, buf + dim);
//		x_norm = buf;
//		y_norm = buf + dim;
//	} else {
//		x_norm = x;
//		y_norm = y;
//	}
//	return (tsReal) (
//		/* Use doubles as long as possible. */
//		acos(ts_vec_dot(x_norm,
//		                y_norm,
//		                dim))
//		* (180.0 / TS_PI) /* radiant to degree */
//		);
//}
//
//void
//ts_vec3_cross(const tsReal *x,
//              const tsReal *y,
//              tsReal *out)
//{
//	tsReal a, b, c;
//	a = x[1] * y[2] - x[2] * y[1];
//	b = x[2] * y[0] - x[0] * y[2];
//	c = x[0] * y[1] - x[1] * y[0];
//	out[0] = a;
//	out[1] = b;
//	out[2] = c;
//}
//
//void
//ts_vec_norm(const tsReal *x,
//            size_t dim,
//            tsReal *out)
//{
//	size_t i;
//	const tsReal m = ts_vec_mag(x, dim);
//	if (m < TS_LENGTH_ZERO) {
//		ts_arr_fill(out, dim, (tsReal) 0.0);
//		return;
//	}
//	for (i = 0; i < dim; i++)
//		out[i] = x[i] / m;
//}
//
//tsReal
//ts_vec_mag(const tsReal *x,
//           size_t dim)
//{
//	size_t i;
//	tsReal sum = 0;
//	for (i = 0; i < dim; i++)
//		sum += (x[i] * x[i]);
//	return (tsReal) sqrt(sum);
//}
//
//void
//ts_vec_mul(const tsReal *x,
//           size_t dim,
//           tsReal val,
//           tsReal *out)
//{
//	size_t i;
//	for (i = 0; i < dim; i++)
//		out[i] = x[i] * val;
//}
/*! @} */

/*! @name Utility Functions
 *
 * @{
 */
int ts_knots_equal(tsReal x,
                   tsReal y)
{
	return fabs(x-y) < TS_KNOT_EPSILON ? 1 : 0;
}

void ts_arr_fill(tsReal *arr,
                 size_t num,
                 tsReal val)
{
	size_t i;
	for (i = 0; i < num; i++)
		arr[i] = val;
}

tsReal ts_distance(const tsReal *x,
                   const tsReal *y,
                   size_t dim)
{
	size_t i;
	tsReal sum = 0;
	for (i = 0; i < dim; i++)
		sum += (x[i] - y[i]) * (x[i] - y[i]);
	return (tsReal) sqrt(sum);
}
/*! @} */

#ifdef _MSC_VER
#pragma warning(pop)
#endif
