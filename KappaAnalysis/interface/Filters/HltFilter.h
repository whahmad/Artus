
#pragma once

#include <memory>

#include "KappaTools/RootTools/RunLumiReader.h"

#include "Artus/Core/interface/FilterBase.h"


/** Filter events for that a previously selected HLT trigger has fired.
 *
 *  The selected HLT trigger has to be defined in the product by the HltProducer.
 *  Therefore this filter cannot meaningfully run as a global pre-filter
 *  which gets an empty product.
 */
class HltFilter: public FilterBase<KappaTypes> {
public:


	virtual std::string GetFilterId() const ARTUS_CPP11_OVERRIDE {
		return "HltFilter";
	}

	virtual bool DoesEventPass(KappaEvent const& event, KappaProduct const& product,
	                           KappaSettings const& settings) const ARTUS_CPP11_OVERRIDE
	{
		if (product.m_selectedHltName.empty())
		{
			// no HLT found
			return false;
		}
		else if (product.m_weights.at("hltPrescaleWeight") < 1.01)
		{
			return event.m_eventMetadata->hltFired(product.m_selectedHltName, event.m_lumiMetadata);;
		}
		else
		{
			if (! settings.GetAllowPrescaledTrigger())
			{
				LOG(FATAL) << "No unprescaled trigger found for event " << event.m_eventMetadata->nEvent
					       << "! Lowest prescale: " << product.m_weights.at("hltPrescaleWeight") << " (\"" << product.m_selectedHltName << "\").";
			}
			return (settings.GetAllowPrescaledTrigger() && event.m_eventMetadata->hltFired(product.m_selectedHltName, event.m_lumiMetadata));
		}
	}

};

