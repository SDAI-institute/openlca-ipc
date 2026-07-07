"""
Tests for DataBuilder class.

Signatures under test:
    create_product_flow(name, description="") -> o.Flow
    create_exchange(flow, amount, is_input, is_quantitative_reference=False,
                    provider=None) -> o.Exchange
    create_process(name, description="", exchanges=None) -> o.Process
"""
import pytest
from unittest.mock import MagicMock
import olca_schema as o
from openlca_ipc.data import DataBuilder


# ---------------------------------------------------------------------------
# Unit-fuzzing fixtures (bug-class prevention for F1: create_exchange must
# never silently force a flow into Mass/kg — it must derive the flow's own
# reference property/unit, whatever that is).
# ---------------------------------------------------------------------------

# (case name, flow-property name, unit-group units [(name, conversion_factor,
# is_reference)], expected reference unit name)
UNIT_FUZZ_CASES = [
    ("mass", "Mass",
     [("kg", 1.0, True), ("g", 0.001, False)], "kg"),
    ("energy", "Net calorific value",
     [("MJ", 1.0, True), ("kWh", 3.6, False)], "MJ"),
    ("volume", "Volume",
     [("m3", 1.0, True), ("l", 0.001, False)], "m3"),
    ("land_use", "Area*time",
     [("m2*a", 1.0, True)], "m2*a"),
    ("transport", "Goods transport (mass*distance)",
     [("t*km", 1.0, True), ("kg*km", 0.001, False)], "t*km"),
    ("items", "Number of items",
     [("Item(s)", 1.0, True)], "Item(s)"),
]


def _make_flow_property_and_units(fp_name, units):
    """Build a FlowProperty + its UnitGroup for a unit-fuzz case."""
    ug = o.UnitGroup(id=f"ug-{fp_name}", name=f"Units of {fp_name}")
    ug.units = [
        o.Unit(id=f"u-{fp_name}-{name}", name=name, conversion_factor=cf,
               is_ref_unit=is_ref)
        for name, cf, is_ref in units
    ]
    fp = o.FlowProperty(id=f"fp-{fp_name}", name=fp_name)
    fp.unit_group = o.Ref(id=f"ug-{fp_name}")
    return fp, ug


def _make_flow_with_property(fp_name, units):
    """A Flow whose sole/reference flow property is the given one."""
    flow = o.Flow(id=f"flow-{fp_name}", name=f"Test flow ({fp_name})")
    flow.flow_type = o.FlowType.PRODUCT_FLOW
    flow.flow_properties = [o.FlowPropertyFactor(
        flow_property=o.Ref(id=f"fp-{fp_name}", name=fp_name),
        conversion_factor=1.0, is_ref_flow_property=True)]
    return flow


class TestDataBuilder:
    """Test suite for DataBuilder."""

    def test_data_builder_initialization(self, mock_ipc_client):
        """Test DataBuilder can be initialized."""
        builder = DataBuilder(mock_ipc_client)
        assert builder is not None
        assert builder.client == mock_ipc_client

    def test_mass_property_cached(self, mock_ipc_client):
        """Mass property is resolved from the client and cached."""
        builder = DataBuilder(mock_ipc_client)
        prop = builder.mass_property
        assert prop.name == "Mass"
        # Second access should reuse the cache, not call get again.
        calls_before = mock_ipc_client.get.call_count
        _ = builder.mass_property
        assert mock_ipc_client.get.call_count == calls_before

    def test_kg_unit(self, mock_ipc_client):
        """kg unit is resolved from the mass property's unit group."""
        builder = DataBuilder(mock_ipc_client)
        assert builder.kg_unit.name == "kg"

    def test_create_product_flow(self, mock_ipc_client):
        """create_product_flow creates a product flow and persists it."""
        builder = DataBuilder(mock_ipc_client)
        flow = builder.create_product_flow(name="Test Product", description="1mm")

        assert isinstance(flow, o.Flow)
        assert flow.name == "Test Product"
        assert flow.flow_type == o.FlowType.PRODUCT_FLOW
        assert flow.id  # a uuid was assigned
        assert flow.flow_properties and flow.flow_properties[0].is_ref_flow_property
        assert mock_ipc_client.put.called

    def test_create_exchange(self, mock_ipc_client, sample_flow):
        """create_exchange builds an exchange with the right amount/direction."""
        builder = DataBuilder(mock_ipc_client)
        exchange = builder.create_exchange(
            flow=sample_flow,
            amount=1.0,
            is_input=True,
            is_quantitative_reference=False,
        )

        assert isinstance(exchange, o.Exchange)
        assert exchange.amount == 1.0
        assert exchange.is_input is True
        assert exchange.is_quantitative_reference is False
        assert exchange.flow.id == sample_flow.id

    def test_create_exchange_with_provider(self, mock_ipc_client, sample_flow, sample_process):
        """create_exchange links a default provider when one is supplied."""
        builder = DataBuilder(mock_ipc_client)
        exchange = builder.create_exchange(
            flow=sample_flow,
            amount=2.0,
            is_input=True,
            provider=sample_process,
        )

        assert exchange.amount == 2.0
        assert exchange.default_provider is not None
        assert exchange.default_provider.id == sample_process.id

    def test_create_exchange_rejects_bad_flow(self, mock_ipc_client):
        """create_exchange raises TypeError for an unsupported flow type."""
        builder = DataBuilder(mock_ipc_client)
        with pytest.raises(TypeError):
            builder.create_exchange(flow="not-a-flow", amount=1.0, is_input=True)

    def test_create_exchange_derives_nonmass_reference_unit(self, mock_ipc_client):
        """v0.4.1: unit/flow_property are derived from the flow's reference
        property, so a transport flow (t*km) is NOT forced to Mass/kg."""
        tkm_group = o.UnitGroup(id="ug-tkm", name="Units of transport")
        tkm = o.Unit(id="u-tkm", name="t*km", conversion_factor=1.0)
        tkm_group.units = [tkm]
        goods = o.FlowProperty(id="fp-goods",
                               name="Goods transport (mass*distance)")
        goods.unit_group = o.Ref(id="ug-tkm")
        flow = o.Flow(id="f-transport", name="transport, lorry")
        flow.flow_type = o.FlowType.PRODUCT_FLOW
        flow.flow_properties = [o.FlowPropertyFactor(
            flow_property=o.Ref(id="fp-goods",
                                name="Goods transport (mass*distance)"),
            conversion_factor=1.0, is_ref_flow_property=True)]

        def _get(model_type, uid=None, *, name=None):
            if model_type is o.Flow:
                return flow
            if model_type is o.FlowProperty:
                return goods
            if model_type is o.UnitGroup:
                return tkm_group
            return None
        mock_ipc_client.get.side_effect = _get

        builder = DataBuilder(mock_ipc_client)
        ex = builder.create_exchange(flow=o.Ref(id="f-transport"),
                                     amount=0.0325, is_input=True)
        assert ex.flow_property.name == "Goods transport (mass*distance)"
        assert ex.unit.name == "t*km"
        assert ex.amount == 0.0325

    def test_create_exchange_stores_formula(self, mock_ipc_client, sample_flow):
        """An optional amount formula is recorded on the exchange."""
        builder = DataBuilder(mock_ipc_client)
        ex = builder.create_exchange(flow=sample_flow, amount=32.5,
                                     is_input=True, formula="0.065*500")
        assert ex.formula == "0.065*500"

    def test_create_exchange_explicit_unit_override(self, mock_ipc_client, sample_flow):
        """Explicit unit/flow_property override the derived reference values."""
        unit = o.Ref(id="u-g", name="g")
        fp = o.Ref(id="fp-mass", name="Mass")
        builder = DataBuilder(mock_ipc_client)
        ex = builder.create_exchange(flow=sample_flow, amount=65.0, is_input=False,
                                     unit=unit, flow_property=fp)
        assert ex.unit.name == "g"
        assert ex.flow_property.name == "Mass"

    # ------------------------------------------------------------------
    # Unit-fuzzing (bug-class prevention for F1): create_exchange must derive
    # each flow's OWN reference property/unit, never silently coerce to
    # Mass/kg — the exact defect that inflated the tutorial's transport
    # exchange ~1000x (0.0325 t*km read back as 32.5 t*km).
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "case_name,fp_name,units,expected_unit",
        UNIT_FUZZ_CASES,
        ids=[c[0] for c in UNIT_FUZZ_CASES],
    )
    def test_create_exchange_derives_unit_for_property_type(
        self, mock_ipc_client, case_name, fp_name, units, expected_unit
    ):
        """Across every flow-property type in the DB, create_exchange must
        pick that flow's own reference unit/property — never Mass/kg unless
        the flow's reference property actually IS Mass."""
        fp, ug = _make_flow_property_and_units(fp_name, units)
        flow = _make_flow_with_property(fp_name, units)

        def _get(model_type, uid=None, *, name=None):
            if model_type is o.Flow:
                return flow
            if model_type is o.FlowProperty:
                return fp
            if model_type is o.UnitGroup:
                return ug
            return None
        mock_ipc_client.get.side_effect = _get

        builder = DataBuilder(mock_ipc_client)
        ex = builder.create_exchange(flow=o.Ref(id=flow.id), amount=1.0, is_input=True)

        assert ex.flow_property.name == fp_name, (
            f"[{case_name}] expected flow_property {fp_name!r}, "
            f"got {ex.flow_property.name!r} (F1-class regression: silent Mass coercion)"
        )
        assert ex.unit.name == expected_unit, (
            f"[{case_name}] expected unit {expected_unit!r}, got {ex.unit.name!r}"
        )
        if fp_name != "Mass":
            assert ex.unit.name != "kg", (
                f"[{case_name}] non-mass flow was silently forced to kg (the F1 bug)"
            )

    def test_create_exchange_reference_unit_chosen_by_flag_not_order(self, mock_ipc_client):
        """Regression guard: the reference unit must be selected via the
        `is_ref_unit` flag, not by list order or by a conversion_factor==1.0
        coincidence. Two units share conversion_factor=1.0; only the SECOND
        one in the list is flagged as the reference — if the code fell back to
        "first unit with conversion_factor==1.0" (or list order) it would pick
        the wrong one."""
        ug = o.UnitGroup(id="ug-ambig", name="Units of ambiguous")
        ug.units = [
            o.Unit(id="u-decoy", name="decoy", conversion_factor=1.0, is_ref_unit=False),
            o.Unit(id="u-real-ref", name="realref", conversion_factor=1.0, is_ref_unit=True),
        ]
        fp = o.FlowProperty(id="fp-ambig", name="Ambiguous property")
        fp.unit_group = o.Ref(id="ug-ambig")
        flow = o.Flow(id="flow-ambig", name="Ambiguous flow")
        flow.flow_type = o.FlowType.PRODUCT_FLOW
        flow.flow_properties = [o.FlowPropertyFactor(
            flow_property=o.Ref(id="fp-ambig", name="Ambiguous property"),
            conversion_factor=1.0, is_ref_flow_property=True)]

        def _get(model_type, uid=None, *, name=None):
            if model_type is o.Flow:
                return flow
            if model_type is o.FlowProperty:
                return fp
            if model_type is o.UnitGroup:
                return ug
            return None
        mock_ipc_client.get.side_effect = _get

        builder = DataBuilder(mock_ipc_client)
        ex = builder.create_exchange(flow=o.Ref(id=flow.id), amount=1.0, is_input=True)
        assert ex.unit.name == "realref"

    # ------------------------------------------------------------------
    # check_mass_balance (tutorial Fig 24: input mass should equal output
    # mass, but openLCA does not enforce this automatically)
    # ------------------------------------------------------------------

    @staticmethod
    def _mass_ex(amount, is_input, unit_name="kg", qref=False):
        ex = o.Exchange()
        ex.amount = amount
        ex.is_input = is_input
        ex.is_quantitative_reference = qref
        ex.flow_property = o.Ref(id="mass-prop-id", name="Mass")
        ex.unit = o.Ref(id=f"{unit_name}-unit-id", name=unit_name)
        return ex

    def test_check_mass_balance_balanced_process_no_warnings(self, mock_ipc_client):
        proc = o.Process(name="Balanced")
        proc.exchanges = [
            self._mass_ex(0.065, False, qref=True),   # output
            self._mass_ex(0.060, True),
            self._mass_ex(0.004, True),
            self._mass_ex(0.001, True),               # inputs sum to 0.065
        ]
        builder = DataBuilder(mock_ipc_client)
        assert builder.check_mass_balance(proc) == []

    def test_check_mass_balance_flags_imbalance(self, mock_ipc_client):
        """The tutorial's own trap: qref output left at 1.0 kg while inputs
        sum to 0.065 kg (Fig 23/25 of the openLCA tutorial)."""
        proc = o.Process(name="PET Granulate Production")
        proc.exchanges = [
            self._mass_ex(1.0, False, qref=True),     # output — NOT corrected
            self._mass_ex(0.060, True),
            self._mass_ex(0.004, True),
            self._mass_ex(0.001, True),               # inputs sum to 0.065
        ]
        builder = DataBuilder(mock_ipc_client)
        warnings = builder.check_mass_balance(proc)
        assert len(warnings) == 1
        assert "PET Granulate Production" in warnings[0]
        assert "1" in warnings[0] and "0.065" in warnings[0]

    def test_check_mass_balance_ignores_non_mass_exchanges(self, mock_ipc_client):
        """A transport (t*km) exchange alongside mass exchanges must not be
        summed in — mixing units would produce a meaningless 'balance'."""
        proc = o.Process(name="Transport-mixed")
        transport_ex = o.Exchange(
            amount=32.5, is_input=True,
            flow_property=o.Ref(id="fp-goods", name="Goods transport (mass*distance)"),
            unit=o.Ref(id="u-tkm", name="t*km"),
        )
        proc.exchanges = [
            self._mass_ex(0.065, False, qref=True),
            self._mass_ex(0.065, True),
            transport_ex,
        ]
        builder = DataBuilder(mock_ipc_client)
        assert builder.check_mass_balance(proc) == []  # balanced ignoring transport

    def test_check_mass_balance_no_mass_exchanges_returns_empty(self, mock_ipc_client):
        proc = o.Process(name="No mass here")
        proc.exchanges = [o.Exchange(
            amount=1.0, is_input=False, is_quantitative_reference=True,
            flow_property=o.Ref(id="fp-items", name="Number of items"),
            unit=o.Ref(id="u-item", name="Item(s)"),
        )]
        builder = DataBuilder(mock_ipc_client)
        assert builder.check_mass_balance(proc) == []

    def test_check_mass_balance_converts_grams_to_kg(self, mock_ipc_client):
        """1000 g input should balance against a 1 kg output."""
        ug = o.UnitGroup(id="unit-group-id", name="Units of mass")
        ug.units = [
            o.Unit(id="kg-unit-id", name="kg", conversion_factor=1.0, is_ref_unit=True),
            o.Unit(id="g-unit-id", name="g", conversion_factor=0.001, is_ref_unit=False),
        ]
        mock_ipc_client.get.side_effect = None

        def _get(model_type, uid=None, *, name=None):
            if model_type is o.FlowProperty:
                return o.FlowProperty(id="mass-prop-id", name="Mass",
                                      unit_group=o.Ref(id="unit-group-id"))
            if model_type is o.UnitGroup:
                return ug
            return None
        mock_ipc_client.get.side_effect = _get

        proc = o.Process(name="Grams check")
        proc.exchanges = [
            self._mass_ex(1.0, False, unit_name="kg", qref=True),
            self._mass_ex(1000.0, True, unit_name="g"),
        ]
        builder = DataBuilder(mock_ipc_client)
        assert builder.check_mass_balance(proc) == []

    def test_check_mass_balance_relative_tolerance_respected(self, mock_ipc_client):
        """A tiny (<0.1%) discrepancy within rel_tol should not warn."""
        proc = o.Process(name="Nearly balanced")
        proc.exchanges = [
            self._mass_ex(0.0650001, False, qref=True),
            self._mass_ex(0.065, True),
        ]
        builder = DataBuilder(mock_ipc_client)
        assert builder.check_mass_balance(proc, rel_tol=1e-3) == []

    def test_create_process(self, mock_ipc_client):
        """create_process creates a process with exchanges and persists it."""
        exchanges = [
            o.Exchange(amount=1.0, is_input=False, is_quantitative_reference=True),
        ]

        builder = DataBuilder(mock_ipc_client)
        process = builder.create_process(name="Test Process", exchanges=exchanges)

        assert isinstance(process, o.Process)
        assert process.name == "Test Process"
        assert process.process_type == o.ProcessType.UNIT_PROCESS
        assert process.exchanges[0].internal_id == 1
        assert process.last_internal_id == 1
        assert mock_ipc_client.put.called

    def test_create_process_warns_on_missing_qref(self, mock_ipc_client, caplog):
        """A process without exactly one quantitative reference logs a warning."""
        exchanges = [
            o.Exchange(amount=1.0, is_input=True, is_quantitative_reference=False),
        ]

        builder = DataBuilder(mock_ipc_client)
        with caplog.at_level("WARNING"):
            process = builder.create_process(name="No Qref", exchanges=exchanges)

        assert isinstance(process, o.Process)
        assert any("qref" in rec.message.lower() for rec in caplog.records)
